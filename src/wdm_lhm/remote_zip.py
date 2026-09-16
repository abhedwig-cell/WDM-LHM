from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen
import json
import struct


EOCD_SIGNATURE = b"PK\x05\x06"
CENTRAL_SIGNATURE = b"PK\x01\x02"


@dataclass(frozen=True)
class RemoteZipIndexConfig:
    timeout_s: int = 60
    tail_bytes: int = 65557  # EOCD max comment (65535) + 22 byte EOCD
    max_central_directory_bytes: int = 50 * 1024 * 1024
    user_agent: str = "wdm-lhm-remote-zip/0.8 (+research; range metadata only)"

    def as_dict(self) -> dict:
        return asdict(self)


class RemoteZipClient:
    def __init__(
        self,
        config: RemoteZipIndexConfig | None = None,
        head_transport: Callable[[str, dict[str, str], int], dict[str, str]] | None = None,
        range_transport: Callable[[str, int, int, dict[str, str], int], tuple[bytes, dict[str, str], int]] | None = None,
    ):
        self.config = config or RemoteZipIndexConfig()
        self.head_transport = head_transport or self._head
        self.range_transport = range_transport or self._range

    @staticmethod
    def _head(url: str, headers: dict[str, str], timeout_s: int) -> dict[str, str]:
        req = Request(url, headers=headers, method="HEAD")
        with urlopen(req, timeout=timeout_s) as r:
            return {k.lower(): v for k, v in r.headers.items()}

    @staticmethod
    def _range(url: str, start: int, end: int, headers: dict[str, str], timeout_s: int) -> tuple[bytes, dict[str, str], int]:
        h = dict(headers)
        h["Range"] = f"bytes={start}-{end}"
        req = Request(url, headers=h, method="GET")
        with urlopen(req, timeout=timeout_s) as r:
            return r.read(), {k.lower(): v for k, v in r.headers.items()}, int(getattr(r, "status", 200))

    def head(self, url: str) -> dict[str, str]:
        return self.head_transport(url, {"User-Agent": self.config.user_agent, "Accept": "*/*"}, self.config.timeout_s)

    def get_range(self, url: str, start: int, end: int) -> tuple[bytes, dict[str, str], int]:
        return self.range_transport(url, start, end, {"User-Agent": self.config.user_agent, "Accept": "application/zip,*/*;q=0.5"}, self.config.timeout_s)


def parse_eocd(tail: bytes, absolute_tail_start: int) -> dict:
    pos = tail.rfind(EOCD_SIGNATURE)
    if pos < 0 or pos + 22 > len(tail):
        raise ValueError("ZIP end-of-central-directory record not found in tail range")
    sig, disk_no, cd_disk, disk_entries, total_entries, cd_size, cd_offset, comment_len = struct.unpack_from(
        "<4s4H2IH", tail, pos
    )
    if sig != EOCD_SIGNATURE:
        raise ValueError("Invalid EOCD signature")
    if pos + 22 + comment_len > len(tail):
        raise ValueError("Incomplete EOCD comment in fetched tail")
    if disk_no != 0 or cd_disk != 0 or disk_entries != total_entries:
        raise ValueError("Multi-disk ZIP archives are not supported")
    if total_entries == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
        raise ValueError("ZIP64 central directory requires explicit support; refusing heuristic parsing")
    return {
        "total_entries": int(total_entries),
        "central_directory_size": int(cd_size),
        "central_directory_offset": int(cd_offset),
        "comment_length": int(comment_len),
        "eocd_absolute_offset": int(absolute_tail_start + pos),
    }


def parse_central_directory(data: bytes, expected_entries: int | None = None) -> list[dict]:
    entries: list[dict] = []
    pos = 0
    fixed = struct.Struct("<4s6H3I5H2I")
    while pos < len(data):
        if len(data) - pos < fixed.size:
            raise ValueError("Truncated ZIP central-directory header")
        fields = fixed.unpack_from(data, pos)
        sig = fields[0]
        if sig != CENTRAL_SIGNATURE:
            raise ValueError(f"Unexpected central-directory signature at byte {pos}: {sig!r}")
        (
            _sig,
            version_made,
            version_needed,
            flags,
            compression_method,
            mod_time,
            mod_date,
            crc32,
            compressed_size,
            uncompressed_size,
            name_len,
            extra_len,
            comment_len,
            disk_start,
            internal_attr,
            external_attr,
            local_header_offset,
        ) = fields
        start = pos + fixed.size
        end_name = start + name_len
        end_extra = end_name + extra_len
        end_comment = end_extra + comment_len
        if end_comment > len(data):
            raise ValueError("Truncated ZIP central-directory variable fields")
        raw_name = data[start:end_name]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = raw_name.decode(encoding, errors="replace")
        if compressed_size == 0xFFFFFFFF or uncompressed_size == 0xFFFFFFFF or local_header_offset == 0xFFFFFFFF:
            raise ValueError(f"ZIP64 entry requires explicit support: {name}")
        entries.append({
            "name": name,
            "compression_method": int(compression_method),
            "compressed_size": int(compressed_size),
            "uncompressed_size": int(uncompressed_size),
            "crc32": int(crc32),
            "flags": int(flags),
            "local_header_offset": int(local_header_offset),
            "is_directory": name.endswith("/"),
        })
        pos = end_comment
    if expected_entries is not None and len(entries) != expected_entries:
        raise ValueError(f"Central-directory entry count mismatch: parsed={len(entries)} expected={expected_entries}")
    return entries


def index_remote_zip(
    url: str,
    output_dir: str | Path,
    config: RemoteZipIndexConfig | None = None,
    *,
    head_transport: Callable[[str, dict[str, str], int], dict[str, str]] | None = None,
    range_transport: Callable[[str, int, int, dict[str, str], int], tuple[bytes, dict[str, str], int]] | None = None,
) -> dict:
    """Index a remote ZIP through HTTP byte ranges without downloading file contents."""
    cfg = config or RemoteZipIndexConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = RemoteZipClient(cfg, head_transport, range_transport)
    head = client.head(url)
    size_raw = head.get("content-length")
    if not size_raw or not str(size_raw).isdigit():
        raise ValueError("Remote ZIP Content-Length is required for range indexing")
    size = int(size_raw)
    if size <= 22:
        raise ValueError("Remote object is too small to be a ZIP archive")

    tail_start = max(0, size - cfg.tail_bytes)
    tail, tail_headers, tail_status = client.get_range(url, tail_start, size - 1)
    content_range = tail_headers.get("content-range", "")
    if tail_status != 206 and not content_range.lower().startswith("bytes"):
        raise ValueError("Server did not honor HTTP Range request; refusing full-object fallback")
    eocd = parse_eocd(tail, tail_start)
    cd_size = eocd["central_directory_size"]
    cd_offset = eocd["central_directory_offset"]
    if cd_size > cfg.max_central_directory_bytes:
        raise ValueError(f"Central directory exceeds configured bound: {cd_size} bytes")
    if cd_offset + cd_size > size:
        raise ValueError("Central directory points outside remote object")

    cd, cd_headers, cd_status = client.get_range(url, cd_offset, cd_offset + cd_size - 1)
    cd_content_range = cd_headers.get("content-range", "")
    if cd_status != 206 and not cd_content_range.lower().startswith("bytes"):
        raise ValueError("Server did not honor central-directory HTTP Range request")
    if len(cd) != cd_size:
        raise ValueError(f"Central-directory byte count mismatch: got={len(cd)} expected={cd_size}")
    entries = parse_central_directory(cd, eocd["total_entries"])

    manifest = {
        "capability": "REMOTE_ZIP_RANGE_INDEX",
        "url": url,
        "config": cfg.as_dict(),
        "remote": {
            "content_length_bytes": size,
            "content_type": head.get("content-type"),
            "accept_ranges": head.get("accept-ranges"),
            "etag": head.get("etag"),
            "last_modified": head.get("last-modified"),
        },
        "eocd": eocd,
        "counts": {
            "entries": len(entries),
            "files": sum(not e["is_directory"] for e in entries),
            "directories": sum(e["is_directory"] for e in entries),
        },
        "entries": entries,
        "qualification_boundary": "Remote ZIP structure only. No archive member content is downloaded or interpreted.",
    }
    (out / "remote_zip_index.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
