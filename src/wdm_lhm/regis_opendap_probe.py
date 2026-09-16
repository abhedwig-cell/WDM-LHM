from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re


REGIS_OPENDAP_ROOT = "https://dinodata.nl/opendap/"
_DATASET_EXTENSIONS = (".nc", ".nc4", ".cdf")
_METADATA_SUFFIXES = (".html", ".dds", ".das", ".info")


@dataclass(frozen=True)
class RegisOpendapProbeConfig:
    root_url: str = REGIS_OPENDAP_ROOT
    max_depth: int = 3
    max_pages: int = 20
    max_page_bytes: int = 512_000
    max_metadata_bytes: int = 2_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-regis-opendap-probe/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)
                break


class RegisOpendapClient:
    def __init__(
        self,
        timeout_s: int = 60,
        user_agent: str = RegisOpendapProbeConfig().user_agent,
        get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get

    @staticmethod
    def _get(
        url: str,
        headers: dict[str, str],
        timeout_s: int,
        max_bytes: int,
    ) -> tuple[bytes, dict[str, str], str]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"OPeNDAP response exceeds guardrail for {url}: > {max_bytes} bytes")
            return (
                payload,
                {k.lower(): v for k, v in response.headers.items()},
                response.geturl(),
            )

    def get(self, url: str, *, max_bytes: int, accept: str = "text/html,text/plain,*/*") -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": accept},
            self.timeout_s,
            max_bytes,
        )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def extract_html_links(payload: bytes, base_url: str) -> list[str]:
    parser = _HrefParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    links: list[str] = []
    seen: set[str] = set()
    for raw in parser.hrefs:
        href, _ = urldefrag(urljoin(base_url, raw))
        if href not in seen:
            seen.add(href)
            links.append(href)
    return links


def normalize_dataset_url(url: str) -> str | None:
    parsed = urlparse(url)
    clean = parsed._replace(query="", fragment="").geturl()
    lower = clean.lower()
    for suffix in _METADATA_SUFFIXES:
        if lower.endswith(suffix):
            candidate = clean[: -len(suffix)]
            if candidate.lower().endswith(_DATASET_EXTENSIONS):
                return candidate
    if lower.endswith(_DATASET_EXTENSIONS):
        return clean
    return None


def _within_root(url: str, *, allowed_hosts: set[str], root_path: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.netloc in allowed_hosts
        and parsed.path.startswith(root_path)
    )


def _looks_like_navigation(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if parsed.query:
        return False
    if normalize_dataset_url(url) is not None:
        return False
    banned = (
        ".zip", ".gz", ".tgz", ".tar", ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".pdf", ".xml", ".json", ".csv", ".dods", ".ascii",
    )
    return not path.endswith(banned)


def _version_hint(text: str) -> bool:
    compact = re.sub(r"[^a-z0-9.]", "", text.lower())
    return any(token in compact for token in ("v02r2s3", "2.2.3", "v2.2.3"))


def probe_regis_opendap(
    output_dir: str | Path,
    config: RegisOpendapProbeConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Discover REGIS OPeNDAP dataset metadata without requesting model values.

    Only HTML directory/catalog pages plus DAP2 DDS/DAS metadata are requested.
    The function deliberately never requests `.dods`, `.ascii`, NetCDF payloads,
    or point/raster values. Dataset identity is discovered first so a later
    workunit can fail closed on version/CRS/dimension semantics before reading
    the two Wageningen pilot columns.
    """
    cfg = config or RegisOpendapProbeConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pages_dir = out / "pages"
    metadata_dir = out / "metadata"
    pages_dir.mkdir(exist_ok=True)
    metadata_dir.mkdir(exist_ok=True)

    client = RegisOpendapClient(cfg.timeout_s, cfg.user_agent, get_transport)
    initial = urlparse(cfg.root_url)
    root_path = initial.path if initial.path.endswith("/") else f"{initial.path}/"
    allowed_hosts = {initial.netloc}

    queue: list[tuple[str, int]] = [(cfg.root_url, 0)]
    seen_pages: set[str] = set()
    page_records: list[dict] = []
    errors: list[dict] = []
    dataset_urls: set[str] = set()
    total_bytes = 0

    while queue and len(seen_pages) < cfg.max_pages:
        requested_url, depth = queue.pop(0)
        if requested_url in seen_pages or depth > cfg.max_depth:
            continue
        try:
            payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_page_bytes)
        except Exception as exc:
            if depth == 0:
                raise
            errors.append({"url": requested_url, "stage": "page", "error": f"{type(exc).__name__}: {exc}"})
            seen_pages.add(requested_url)
            continue

        final = urlparse(final_url)
        allowed_hosts.add(final.netloc)
        seen_pages.add(requested_url)
        seen_pages.add(final_url)
        total_bytes += len(payload)
        digest = _sha256(payload)
        (pages_dir / f"{digest}.html").write_bytes(payload)
        links = extract_html_links(payload, final_url)
        page_records.append({
            "requested_url": requested_url,
            "final_url": final_url,
            "depth": depth,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": headers.get("content-type"),
            "link_count": len(links),
        })

        for href in links:
            if not _within_root(href, allowed_hosts=allowed_hosts, root_path=root_path):
                continue
            dataset_url = normalize_dataset_url(href)
            if dataset_url is not None and "regis" in dataset_url.lower():
                dataset_urls.add(dataset_url)
                continue
            if depth < cfg.max_depth and _looks_like_navigation(href) and href not in seen_pages:
                queue.append((href, depth + 1))

    dataset_records: list[dict] = []
    for dataset_url in sorted(dataset_urls):
        record: dict = {
            "dataset_url": dataset_url,
            "dds": None,
            "das": None,
            "dap2_metadata_available": False,
            "version_v02r2s3_hint": False,
        }
        combined_text = dataset_url
        for suffix, key in ((".dds", "dds"), (".das", "das")):
            url = f"{dataset_url}{suffix}"
            try:
                payload, headers, final_url = client.get(
                    url,
                    max_bytes=cfg.max_metadata_bytes,
                    accept="text/plain,*/*",
                )
                total_bytes += len(payload)
                digest = _sha256(payload)
                output_name = f"{digest}{suffix}.txt"
                (metadata_dir / output_name).write_bytes(payload)
                text = payload.decode("utf-8", errors="replace")
                combined_text += "\n" + text
                record[key] = {
                    "requested_url": url,
                    "final_url": final_url,
                    "bytes": len(payload),
                    "sha256": digest,
                    "content_type": headers.get("content-type"),
                    "artifact_file": f"metadata/{output_name}",
                }
            except Exception as exc:
                errors.append({"url": url, "stage": key, "error": f"{type(exc).__name__}: {exc}"})
        record["dap2_metadata_available"] = bool(record["dds"] and record["das"])
        record["version_v02r2s3_hint"] = _version_hint(combined_text)
        dataset_records.append(record)

    manifest = {
        "capability": "STAGE_B_REGIS_OPENDAP_DISCOVERY",
        "config": cfg.as_dict(),
        "pages": page_records,
        "datasets": dataset_records,
        "errors": errors,
        "counts": {
            "pages": len(page_records),
            "dataset_candidates": len(dataset_records),
            "dap2_metadata_candidates": sum(bool(r["dap2_metadata_available"]) for r in dataset_records),
            "v02r2s3_hints": sum(bool(r["version_v02r2s3_hint"]) for r in dataset_records),
            "response_bytes": total_bytes,
        },
        "guardrails": {
            "value_requests_performed": False,
            "dods_requests_performed": False,
            "ascii_requests_performed": False,
            "netcdf_payload_downloaded": False,
            "hydrogeological_interpretation_performed": False,
            "admission_decision_performed": False,
        },
        "qualification_boundary": (
            "Service and dataset metadata discovery only. No REGIS raster/column value is read and no Stage-B freatic admission claim is made."
        ),
    }
    (out / "regis_opendap_probe_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
