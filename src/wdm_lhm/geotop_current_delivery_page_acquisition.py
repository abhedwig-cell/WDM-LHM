from __future__ import annotations

from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import hashlib
import json


CURRENT_DELIVERY_URL = "https://www.dinoloket.nl/bekijken-en-aanvragen-geotop"
OFFICIAL_HOSTS = {"www.dinoloket.nl", "dinoloket.nl", "www.tno.nl", "tno.nl"}
MARKERS = (
    "GeoTOP",
    "1.6.1",
    "referentielijst",
    "referentielijsten",
    "REF_GTP_LITHO_CLASS",
    "REF_GTP_STR_UNIT",
    "lithoklasse",
    "lithostrat",
    "modelbestanden",
    "download",
    "zip",
    "csv",
    "xlsx",
)


@dataclass(frozen=True)
class GeoTopCurrentDeliveryPageConfig:
    url: str = CURRENT_DELIVERY_URL
    max_response_bytes: int = 3_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-current-delivery/0.8 (+research; one qualified official page only)"

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


class GeoTopCurrentDeliveryPageClient:
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
                raise ValueError(f"GeoTOP current-delivery page exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/html,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _validate_config(cfg: GeoTopCurrentDeliveryPageConfig) -> None:
    if cfg.url != CURRENT_DELIVERY_URL:
        raise ValueError("GeoTOP current-delivery discovery is pinned to one qualified Gate-2 URL")


def _validate_final_url(final_url: str) -> None:
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        raise ValueError("GeoTOP current-delivery final URL is not HTTPS")
    if parsed.netloc.lower() not in OFFICIAL_HOSTS:
        raise ValueError("GeoTOP current-delivery redirect escaped official DINOloket/TNO hosts")
    if parsed.query or parsed.fragment:
        raise ValueError("GeoTOP current-delivery final URL contains unexpected query or fragment")


def _inventory_links(base_url: str, html_text: str) -> list[dict]:
    parser = _HrefParser()
    parser.feed(html_text)
    records: dict[str, dict] = {}
    for href in parser.hrefs:
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        host = parsed.netloc.lower()
        if host not in OFFICIAL_HOSTS:
            continue
        records[absolute] = {
            "url": absolute,
            "host": host,
            "scheme": parsed.scheme,
            "path": parsed.path,
            "suffix": Path(parsed.path).suffix.lower(),
        }
    return [records[url] for url in sorted(records)]


def acquire_geotop_current_delivery_page(
    output_dir: str | Path,
    config: GeoTopCurrentDeliveryPageConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire one qualified official GeoTOP current-delivery page and inventory links only."""
    cfg = config or GeoTopCurrentDeliveryPageConfig()
    _validate_config(cfg)
    client = GeoTopCurrentDeliveryPageClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(cfg.url, max_bytes=cfg.max_response_bytes)
    if not payload:
        raise ValueError("GeoTOP current-delivery page response is empty")
    _validate_final_url(final_url)
    content_type = headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"Unexpected GeoTOP current-delivery content type: {content_type!r}")

    text = payload.decode("utf-8", errors="strict")
    links = _inventory_links(final_url, text)
    hits = [marker for marker in MARKERS if marker.casefold() in text.casefold()]
    candidate_links = [
        rec for rec in links
        if rec["suffix"] in {".csv", ".xlsx", ".xls", ".zip", ".json", ".xml"}
        or any(token in rec["path"].casefold() for token in ("referentie", "modelbestand", "download", "geotop"))
    ]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "geotop_current_delivery_page.html"
    (out / raw_name).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    manifest = {
        "capability": "STAGE_B_GEOTOP_161_CURRENT_DELIVERY_AUTHORITY_DISCOVERY",
        "state": "OFFICIAL_CURRENT_DELIVERY_PAGE_ACQUIRED_LINKS_NOT_FOLLOWED",
        "config": cfg.as_dict(),
        "request": {"url": cfg.url, "final_url": final_url},
        "response": {
            "artifact_file": raw_name,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": content_type,
        },
        "marker_hits": hits,
        "official_links": links,
        "candidate_authority_links": candidate_links,
        "guardrails": {
            "single_gate2_discovered_url_only": True,
            "official_redirect_only": True,
            "links_followed": False,
            "generic_web_search_performed": False,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_current_delivery_page_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
