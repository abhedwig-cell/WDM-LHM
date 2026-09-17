from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import hashlib
import json


DOCUMENTS = {
    "v16_supplement": {
        "url": "https://www.dinoloket.nl/sites/default/files/2023-10/R11636%20Totstandkomingsrapport%20GeoTOP%20-%20aanvullingen%20bij%20versie%20v1.6.pdf",
        "output_name": "geotop_v16_supplement.pdf",
    },
    "v161_small_release": {
        "url": "https://www.dinoloket.nl/sites/default/files/2025-03/Toelichting%20bij%20kleine%20release%20GeoTOP%20v1.6.1%20-%20Modelonzekerheid%20van%20geologische%20eenheid.pdf",
        "output_name": "geotop_v161_small_release.pdf",
    },
    "general_report": {
        "url": "https://www.dinoloket.nl/sites/default/files/docs/geotop/R11655%20Totstandkomingsrapport%20GeoTOP.pdf",
        "output_name": "geotop_general_report.pdf",
    },
}
OFFICIAL_HOSTS = {"www.dinoloket.nl", "dinoloket.nl"}


@dataclass(frozen=True)
class GeoTopAuthorityDocumentConfig:
    max_document_bytes: int = 30 * 1024 * 1024
    timeout_s: int = 90
    user_agent: str = "wdm-lhm-geotop-authority-documents/0.8 (+research; bounded official documents only)"

    def as_dict(self) -> dict:
        return asdict(self)


class GeoTopAuthorityDocumentClient:
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
                raise ValueError(f"GeoTOP authority document exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "application/pdf"},
            self.timeout_s,
            max_bytes,
        )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_final_url(final_url: str) -> None:
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        raise ValueError("GeoTOP authority document final URL is not HTTPS")
    if parsed.netloc.lower() not in OFFICIAL_HOSTS:
        raise ValueError("GeoTOP authority document escaped official DINOloket host")
    if not parsed.path.lower().endswith(".pdf"):
        raise ValueError("GeoTOP authority document final resource is not a PDF path")
    if parsed.query or parsed.fragment:
        raise ValueError("GeoTOP authority document final URL contains unexpected query or fragment")


def _validate_pdf(payload: bytes, content_type: str) -> None:
    if not payload.startswith(b"%PDF-"):
        raise ValueError("GeoTOP authority document does not have a PDF signature")
    if "pdf" not in content_type.lower():
        raise ValueError(f"Unexpected GeoTOP authority document content type: {content_type!r}")


def acquire_geotop_authority_documents(
    output_dir: str | Path,
    config: GeoTopAuthorityDocumentConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire the fixed official document set surfaced by the dataset-referenced GeoTOP page.

    This gate is acquisition-only. PDFs are persisted byte-for-byte with hashes.
    No PDF text extraction, code-table extraction, geological interpretation or
    Stage-B admission decision is performed here.
    """
    cfg = config or GeoTopAuthorityDocumentConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = GeoTopAuthorityDocumentClient(cfg.timeout_s, cfg.user_agent, get_transport)

    records: dict[str, dict] = {}
    for key, spec in DOCUMENTS.items():
        requested_url = spec["url"]
        payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_document_bytes)
        if not payload:
            raise ValueError(f"GeoTOP authority document response is empty: {key}")
        _validate_final_url(final_url)
        content_type = headers.get("content-type", "")
        _validate_pdf(payload, content_type)

        output_name = spec["output_name"]
        (out / output_name).write_bytes(payload)
        records[key] = {
            "requested_url": requested_url,
            "final_url": final_url,
            "output_name": output_name,
            "bytes": len(payload),
            "sha256": _sha256(payload),
            "content_type": content_type,
            "content_length": headers.get("content-length"),
            "last_modified": headers.get("last-modified"),
        }

    manifest = {
        "capability": "STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY_DOCUMENT_ACQUISITION",
        "state": "BOUNDED_OFFICIAL_AUTHORITY_DOCUMENTS_ACQUIRED_NOT_ANALYSED",
        "config": cfg.as_dict(),
        "documents": records,
        "source_selection": {
            "selection_basis": "explicit links on the exact dataset-referenced DINOloket GeoTOP page qualified in Gate 2",
            "document_keys": list(DOCUMENTS),
            "document_count": len(DOCUMENTS),
        },
        "guardrails": {
            "official_dinoloket_documents_only": True,
            "fixed_document_set_only": True,
            "pdf_bytes_persisted_before_analysis": True,
            "pdf_text_extracted": False,
            "code_tables_extracted": False,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "screen_correlation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_authority_document_acquisition_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
