from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json


DATASET_URL = "https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc"
RESOURCE_SUFFIXES = (".html", ".info")
OFFICIAL_HOSTS = {
    "www.dinodata.nl",
    "dinodata.nl",
    "www.dinoloket.nl",
    "dinoloket.nl",
    "www.tno.nl",
    "tno.nl",
}
MARKERS = ("1.6.1", "GeoTOP", "lithok", "lithostrat", "strat", "code")


@dataclass(frozen=True)
class GeoTopAuthorityDiscoveryConfig:
    dataset_url: str = DATASET_URL
    max_resource_bytes: int = 2_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-authority-discovery/0.8 (+research; official TNO/DINOloket resources only)"

    def as_dict(self) -> dict:
        return asdict(self)


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


class GeoTopAuthorityDiscoveryClient:
    def __init__(
        self,
        timeout_s: int,
        user_agent: str,
        get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get

    @staticmethod
    def _get(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"GeoTOP authority resource exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/html,text/plain,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _validate_dataset_url(dataset_url: str) -> None:
    parsed = urlparse(dataset_url)
    if parsed.scheme != "https" or parsed.netloc != "www.dinodata.nl":
        raise ValueError("GeoTOP authority discovery escaped fixed official host")
    if parsed.path != "/opendap/hyrax/GeoTOP/geotop.nc" or parsed.query or parsed.fragment:
        raise ValueError("GeoTOP authority discovery dataset path drift")


def _validate_final_url(requested_url: str, final_url: str) -> None:
    req = urlparse(requested_url)
    final = urlparse(final_url)
    if final.scheme != "https" or final.netloc != "www.dinodata.nl":
        raise ValueError("GeoTOP authority discovery redirect escaped fixed host")
    if final.path != req.path or final.query or final.fragment:
        raise ValueError("GeoTOP authority discovery redirect changed fixed resource")


def _official_links(base_url: str, html_text: str) -> list[str]:
    parser = _HrefParser()
    parser.feed(html_text)
    links: set[str] = set()
    for href in parser.hrefs:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme == "https" and parsed.netloc.lower() in OFFICIAL_HOSTS:
            links.add(absolute)
    return sorted(links)


def acquire_geotop_authority_discovery(
    output_dir: str | Path,
    config: GeoTopAuthorityDiscoveryConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire exact official dataset service resources and inventory links only."""
    cfg = config or GeoTopAuthorityDiscoveryConfig()
    _validate_dataset_url(cfg.dataset_url)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = GeoTopAuthorityDiscoveryClient(cfg.timeout_s, cfg.user_agent, get_transport)

    resources: dict[str, dict] = {}
    official_links: set[str] = set()
    marker_hits: dict[str, list[str]] = {}

    for suffix in RESOURCE_SUFFIXES:
        requested_url = f"{cfg.dataset_url}{suffix}"
        payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_resource_bytes)
        if not payload:
            raise ValueError(f"empty GeoTOP authority resource: {suffix}")
        if len(payload) > cfg.max_resource_bytes:
            raise ValueError(f"GeoTOP authority resource exceeds guardrail: {len(payload)} > {cfg.max_resource_bytes}")
        _validate_final_url(requested_url, final_url)
        text = payload.decode("utf-8", errors="strict")
        name = "geotop_service" + suffix + ".txt"
        (out / name).write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        hits = [marker for marker in MARKERS if marker.lower() in text.lower()]
        marker_hits[suffix] = hits
        if suffix == ".html":
            official_links.update(_official_links(final_url, text))
        resources[suffix[1:]] = {
            "requested_url": requested_url,
            "final_url": final_url,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": headers.get("content-type"),
            "artifact_file": name,
        }

    manifest = {
        "capability": "STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY_DISCOVERY",
        "state": "OFFICIAL_DATASET_SERVICE_RESOURCES_ACQUIRED_NOT_INTERPRETED",
        "config": cfg.as_dict(),
        "resources": resources,
        "official_links": sorted(official_links),
        "marker_hits": marker_hits,
        "guardrails": {
            "official_dataset_resources_only": True,
            "discovered_links_followed": False,
            "third_party_resources_requested": False,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_codebook_authority_discovery_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
