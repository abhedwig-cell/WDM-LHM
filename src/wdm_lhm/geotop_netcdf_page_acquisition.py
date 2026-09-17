from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
import hashlib
import json

from .geotop_model_files_page_acquisition import (
    GeoTopModelFilesPageClient,
    _PageParser,
    _normalise_forms,
    _normalise_official_links,
    _validate_final_url,
)


NETCDF_PAGE_URL = "https://www.dinoloket.nl/modelbestanden-aanvragen/netcdf"
MARKERS = (
    "GeoTOP",
    "NetCDF",
    "referentielijst",
    "referentielijsten",
    "lithoklasse",
    "geologische eenheid",
    "download",
    "zip",
    "csv",
    "xlsx",
    "opendap",
)


@dataclass(frozen=True)
class GeoTopNetcdfPageConfig:
    url: str = NETCDF_PAGE_URL
    max_response_bytes: int = 3_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-netcdf-page/0.8 (+research; inspect only; no request submit)"

    def as_dict(self) -> dict:
        return asdict(self)


def acquire_geotop_netcdf_page(
    output_dir: str | Path,
    config: GeoTopNetcdfPageConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    cfg = config or GeoTopNetcdfPageConfig()
    if cfg.url != NETCDF_PAGE_URL:
        raise ValueError("GeoTOP NetCDF discovery is pinned to the exact Gate-3D child URL")
    client = GeoTopModelFilesPageClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(cfg.url, max_bytes=cfg.max_response_bytes)
    if not payload:
        raise ValueError("GeoTOP NetCDF page response is empty")
    _validate_final_url(final_url)
    content_type = headers.get("content-type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"Unexpected GeoTOP NetCDF page content type: {content_type!r}")

    text = payload.decode("utf-8", errors="strict")
    parser = _PageParser()
    parser.feed(text)
    links = _normalise_official_links(final_url, parser.hrefs)
    forms = _normalise_forms(final_url, parser.forms)
    marker_hits = [m for m in MARKERS if m.casefold() in text.casefold()]
    candidates = [
        rec for rec in links
        if rec["suffix"] in {".csv", ".xlsx", ".xls", ".zip", ".json", ".xml", ".nc"}
        or any(token in rec["path"].casefold() for token in ("referentie", "download", "opendap", "geotop", "netcdf"))
    ]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "geotop_netcdf_page.html"
    (out / raw_name).write_bytes(payload)
    manifest = {
        "capability": "STAGE_B_GEOTOP_161_NETCDF_AUTHORITY_DISCOVERY",
        "state": "OFFICIAL_NETCDF_PAGE_ACQUIRED_NO_ACTIONS_INVOKED",
        "config": cfg.as_dict(),
        "request": {"url": cfg.url, "final_url": final_url},
        "response": {
            "artifact_file": raw_name,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "content_type": content_type,
        },
        "marker_hits": marker_hits,
        "official_links": links,
        "candidate_authority_links": candidates,
        "forms": forms,
        "guardrails": {
            "exact_gate3d_child_url_only": True,
            "links_followed": False,
            "forms_submitted": False,
            "form_actions_invoked": False,
            "data_request_performed": False,
            "generic_web_search_performed": False,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_netcdf_page_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
