from __future__ import annotations

from pathlib import Path
from typing import Callable
import hashlib
import json
import re
import subprocess


EXPECTED_DOCUMENTS = {
    "v16_supplement": {
        "input_name": "geotop_v16_supplement.pdf",
        "sha256": "d35108ce0749007935565778392dd4d4d32a40ad08d48f6c5c37d833b0746ad3",
    },
    "v161_small_release": {
        "input_name": "geotop_v161_small_release.pdf",
        "sha256": "9b50b3a2d1b02d3292ef4f5259a6716f1f0aa0ae11341ad5b0eb9c80a4a5ba83",
    },
    "general_report": {
        "input_name": "geotop_general_report.pdf",
        "sha256": "9c72f77d4ec84272ec007e7c31e8f60877aec10d5abf1d77fd9b0cdb11bf3cba",
    },
}

MARKERS = (
    "GeoTOP",
    "1.6.1",
    "1.6",
    "lithoklasse",
    "lithostrat",
    "lithok",
    "strat",
    "code",
    "codes",
    "legenda",
    "klasse",
)

OBSERVED_CODES = {
    "strat": (1000, 3030, 3100, 4100, 5000, 5120),
    "lithok": (0, 1, 2, 3, 5, 6, 7),
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _default_extractor(pdf_path: Path, text_path: Path) -> None:
    subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf_path), str(text_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _default_extractor_identity() -> str:
    result = subprocess.run(
        ["pdftotext", "-v"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    identity = (result.stderr or result.stdout).strip().splitlines()
    return identity[0] if identity else "pdftotext version unknown"


def _token_count(text: str, token: str) -> int:
    return len(re.findall(rf"(?<!\d){re.escape(token)}(?!\d)", text))


def _marker_hits(text: str) -> list[str]:
    lower = text.casefold()
    return [marker for marker in MARKERS if marker.casefold() in lower]


def _observed_code_occurrences(text: str) -> dict[str, dict[str, int]]:
    return {
        family: {str(code): _token_count(text, str(code)) for code in codes}
        for family, codes in OBSERVED_CODES.items()
    }


def _page_index(text: str) -> list[dict]:
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    if not pages:
        raise ValueError("text extractor produced no page content")

    records: list[dict] = []
    for page_number, page_text in enumerate(pages, start=1):
        page_bytes = page_text.encode("utf-8")
        records.append(
            {
                "page": page_number,
                "characters": len(page_text),
                "sha256": _sha256_bytes(page_bytes),
                "marker_hits": _marker_hits(page_text),
                "observed_code_occurrences": _observed_code_occurrences(page_text),
            }
        )
    return records


def extract_geotop_authority_text(
    source_dir: str | Path,
    output_dir: str | Path,
    *,
    extractor: Callable[[Path, Path], None] | None = None,
    extractor_identity: str | None = None,
) -> dict:
    """Verify Gate-3A PDFs and extract page-preserving text without semantic code translation."""
    source = Path(source_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    run_extractor = extractor or _default_extractor
    identity = extractor_identity or _default_extractor_identity()

    records: dict[str, dict] = {}
    for key, spec in EXPECTED_DOCUMENTS.items():
        pdf_path = source / spec["input_name"]
        if not pdf_path.exists():
            raise ValueError(f"missing qualified GeoTOP authority PDF: {key}")
        pdf_bytes = pdf_path.read_bytes()
        actual_sha = _sha256_bytes(pdf_bytes)
        if actual_sha != spec["sha256"]:
            raise ValueError(
                f"GeoTOP authority PDF SHA drift for {key}: {actual_sha} != {spec['sha256']}"
            )
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError(f"qualified GeoTOP authority input is not a PDF: {key}")

        text_name = f"{key}.txt"
        text_path = out / text_name
        run_extractor(pdf_path, text_path)
        if not text_path.exists():
            raise ValueError(f"text extractor produced no output for {key}")
        text_bytes = text_path.read_bytes()
        if not text_bytes:
            raise ValueError(f"text extractor produced empty output for {key}")
        text = text_bytes.decode("utf-8", errors="strict")
        pages = _page_index(text)

        records[key] = {
            "source_file": spec["input_name"],
            "source_sha256": actual_sha,
            "text_file": text_name,
            "text_bytes": len(text_bytes),
            "text_sha256": _sha256_bytes(text_bytes),
            "characters": len(text),
            "page_count": len(pages),
            "page_index": pages,
            "marker_hits": _marker_hits(text),
            "observed_code_occurrences": _observed_code_occurrences(text),
        }

    manifest = {
        "capability": "STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY_TEXT_EXTRACTION",
        "state": "QUALIFIED_SOURCE_TEXT_EXTRACTED_NOT_SEMANTICALLY_ADJUDICATED",
        "extractor_identity": identity,
        "expected_source_sha256": {
            key: spec["sha256"] for key, spec in EXPECTED_DOCUMENTS.items()
        },
        "documents": records,
        "observed_codes": {family: list(codes) for family, codes in OBSERVED_CODES.items()},
        "guardrails": {
            "exact_gate_3a_hashes_required": True,
            "fixed_document_set_only": True,
            "text_extraction_only": True,
            "page_index_preserved": True,
            "marker_inventory_only": True,
            "code_translation_performed": False,
            "version_compatibility_established": False,
            "geological_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "screen_correlation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_authority_text_extraction_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
