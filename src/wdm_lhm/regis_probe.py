from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import xml.etree.ElementTree as ET


REGIS_ATOM_URL = "https://service.pdok.nl/tno/bro-regis-ii/atom/index.xml"


@dataclass(frozen=True)
class RegisProbeConfig:
    atom_url: str = REGIS_ATOM_URL
    max_depth: int = 3
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-regis-probe/0.8 (+research; public PDOK service)"

    def as_dict(self) -> dict:
        return asdict(self)


class RegisProbeClient:
    def __init__(
        self,
        timeout_s: int = 60,
        user_agent: str = RegisProbeConfig().user_agent,
        get_transport: Callable[[str, dict[str, str], int], tuple[bytes, dict[str, str]]] | None = None,
        head_transport: Callable[[str, dict[str, str], int], dict[str, str]] | None = None,
    ):
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get
        self.head_transport = head_transport or self._head

    @staticmethod
    def _get(url: str, headers: dict[str, str], timeout_s: int) -> tuple[bytes, dict[str, str]]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as r:
            return r.read(), {k.lower(): v for k, v in r.headers.items()}

    @staticmethod
    def _head(url: str, headers: dict[str, str], timeout_s: int) -> dict[str, str]:
        req = Request(url, headers=headers, method="HEAD")
        with urlopen(req, timeout=timeout_s) as r:
            return {k.lower(): v for k, v in r.headers.items()}

    def get(self, url: str) -> tuple[bytes, dict[str, str]]:
        return self.get_transport(url, {"User-Agent": self.user_agent, "Accept": "application/atom+xml,application/xml,text/xml,*/*"}, self.timeout_s)

    def head(self, url: str) -> dict[str, str]:
        return self.head_transport(url, {"User-Agent": self.user_agent, "Accept": "*/*"}, self.timeout_s)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_atom_document(payload: bytes, base_url: str) -> dict:
    root = ET.fromstring(payload)
    metadata: dict[str, str | None] = {"title": None, "id": None, "updated": None}
    links: list[dict] = []

    for elem in root.iter():
        name = _local(elem.tag)
        if name in metadata and metadata[name] is None and elem.text:
            metadata[name] = elem.text.strip()
        if name == "link":
            href = elem.attrib.get("href")
            if not href:
                continue
            links.append({
                "href": urljoin(base_url, href),
                "rel": elem.attrib.get("rel", ""),
                "type": elem.attrib.get("type", ""),
                "title": elem.attrib.get("title", ""),
                "hreflang": elem.attrib.get("hreflang", ""),
            })

    return {"metadata": metadata, "links": links}


def _is_atom_link(link: dict) -> bool:
    href = link["href"].lower()
    typ = str(link.get("type", "")).lower()
    return (
        href.endswith(".xml")
        or "atom+xml" in typ
        or ("xml" in typ and not any(href.endswith(s) for s in (".zip", ".7z", ".gz")))
    )


def _is_download_link(link: dict) -> bool:
    href = link["href"].lower().split("?", 1)[0]
    typ = str(link.get("type", "")).lower()
    rel = str(link.get("rel", "")).lower()
    return (
        any(href.endswith(s) for s in (".zip", ".7z", ".gz", ".tar", ".tgz"))
        or "zip" in typ
        or "octet-stream" in typ
        or rel == "enclosure"
    )


def probe_regis_delivery(
    output_dir: str | Path,
    config: RegisProbeConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int], tuple[bytes, dict[str, str]]] | None = None,
    head_transport: Callable[[str, dict[str, str], int], dict[str, str]] | None = None,
) -> dict:
    """Inspect the public REGIS II ATOM delivery without downloading model archives.

    This function qualifies acquisition metadata only. It does not interpret
    hydrogeology and does not download large REGIS model files.
    """
    cfg = config or RegisProbeConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_dir = out / "atom"
    raw_dir.mkdir(exist_ok=True)
    client = RegisProbeClient(cfg.timeout_s, cfg.user_agent, get_transport, head_transport)

    start_host = urlparse(cfg.atom_url).netloc
    queue: list[tuple[str, int]] = [(cfg.atom_url, 0)]
    seen: set[str] = set()
    feeds: list[dict] = []
    download_map: dict[str, dict] = {}

    while queue:
        url, depth = queue.pop(0)
        if url in seen or depth > cfg.max_depth:
            continue
        seen.add(url)
        payload, headers = client.get(url)
        sha = hashlib.sha256(payload).hexdigest()
        (raw_dir / f"{sha}.xml").write_bytes(payload)
        doc = parse_atom_document(payload, url)
        feeds.append({
            "url": url,
            "depth": depth,
            "sha256": sha,
            "bytes": len(payload),
            "content_type": headers.get("content-type"),
            **doc["metadata"],
            "link_count": len(doc["links"]),
        })

        for link in doc["links"]:
            href = link["href"]
            if _is_download_link(link):
                download_map.setdefault(href, dict(link))
                continue
            if depth < cfg.max_depth and _is_atom_link(link) and urlparse(href).netloc == start_host:
                if href not in seen:
                    queue.append((href, depth + 1))

    downloads: list[dict] = []
    for href, link in sorted(download_map.items()):
        headers: dict[str, str] = {}
        error: str | None = None
        try:
            headers = client.head(href)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        size = headers.get("content-length")
        downloads.append({
            **link,
            "content_length_bytes": int(size) if size and str(size).isdigit() else None,
            "content_type_head": headers.get("content-type"),
            "last_modified": headers.get("last-modified"),
            "etag": headers.get("etag"),
            "head_error": error,
        })

    manifest = {
        "capability": "STAGE_B_REGIS_ACQUISITION_PROBE",
        "config": cfg.as_dict(),
        "feeds": feeds,
        "downloads": downloads,
        "counts": {"feeds": len(feeds), "download_candidates": len(downloads)},
        "qualification_boundary": (
            "Acquisition metadata only. No archive is downloaded and no hydrogeological or freatic admission claim is made."
        ),
    }
    (out / "regis_probe_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
