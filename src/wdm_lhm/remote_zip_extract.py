from __future__ import annotations

from pathlib import Path
from typing import Callable
import binascii
import struct
import zlib

from .remote_zip import RemoteZipClient, RemoteZipIndexConfig


LOCAL_SIGNATURE = b"PK\x03\x04"


def extract_remote_zip_member(
    url: str,
    entry: dict,
    output_path: str | Path,
    config: RemoteZipIndexConfig | None = None,
    *,
    head_transport: Callable[[str, dict[str, str], int], dict[str, str]] | None = None,
    range_transport: Callable[[str, int, int, dict[str, str], int], tuple[bytes, dict[str, str], int]] | None = None,
    max_uncompressed_bytes: int = 10 * 1024 * 1024,
) -> Path:
    """Extract one bounded member from a remote ZIP using HTTP ranges.

    Supported compression methods are STORE (0) and DEFLATE (8). The caller
    supplies an entry from the already qualified remote ZIP central-directory
    index. Large members are refused before download.
    """
    usize = int(entry["uncompressed_size"])
    csize = int(entry["compressed_size"])
    if usize > max_uncompressed_bytes:
        raise ValueError(f"Member exceeds bounded extraction limit: {usize} bytes")
    if csize < 0 or usize < 0:
        raise ValueError("Invalid ZIP member size")

    cfg = config or RemoteZipIndexConfig()
    client = RemoteZipClient(cfg, head_transport, range_transport)
    offset = int(entry["local_header_offset"])

    # Local file header is 30 fixed bytes followed by file name and extra field.
    header, headers, status = client.get_range(url, offset, offset + 29)
    if status != 206 and not headers.get("content-range", "").lower().startswith("bytes"):
        raise ValueError("Server did not honor local-header Range request")
    if len(header) != 30:
        raise ValueError("Truncated local ZIP header")
    (
        sig,
        version_needed,
        flags,
        compression_method,
        mod_time,
        mod_date,
        crc32_local,
        compressed_size_local,
        uncompressed_size_local,
        name_len,
        extra_len,
    ) = struct.unpack("<4s5H3I2H", header)
    if sig != LOCAL_SIGNATURE:
        raise ValueError("Invalid local ZIP header signature")
    if compression_method != int(entry["compression_method"]):
        raise ValueError("Local/central compression-method mismatch")

    data_offset = offset + 30 + int(name_len) + int(extra_len)
    if csize == 0:
        compressed = b""
    else:
        compressed, data_headers, data_status = client.get_range(url, data_offset, data_offset + csize - 1)
        if data_status != 206 and not data_headers.get("content-range", "").lower().startswith("bytes"):
            raise ValueError("Server did not honor member-data Range request")
        if len(compressed) != csize:
            raise ValueError(f"Compressed member byte count mismatch: got={len(compressed)} expected={csize}")

    if compression_method == 0:
        payload = compressed
    elif compression_method == 8:
        payload = zlib.decompress(compressed, -15)
    else:
        raise ValueError(f"Unsupported ZIP compression method: {compression_method}")

    if len(payload) != usize:
        raise ValueError(f"Uncompressed member byte count mismatch: got={len(payload)} expected={usize}")
    crc = binascii.crc32(payload) & 0xFFFFFFFF
    if crc != int(entry["crc32"]):
        raise ValueError(f"CRC mismatch for {entry['name']}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return out
