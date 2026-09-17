from pathlib import Path

import pytest

from wdm_lhm.geotop_authority_document_acquisition import (
    DOCUMENTS,
    GeoTopAuthorityDocumentConfig,
    acquire_geotop_authority_documents,
)


def _pdf(label: str) -> bytes:
    return b"%PDF-1.7\n" + label.encode("utf-8") + b"\n%%EOF\n"


def test_acquires_exact_fixed_document_set(tmp_path: Path) -> None:
    calls: list[str] = []

    def transport(url, headers, timeout_s, max_bytes):
        calls.append(url)
        payload = _pdf(url.rsplit("/", 1)[-1])
        return payload, {"content-type": "application/pdf", "content-length": str(len(payload))}, url

    manifest = acquire_geotop_authority_documents(tmp_path, get_transport=transport)

    assert calls == [DOCUMENTS[k]["url"] for k in DOCUMENTS]
    assert manifest["state"] == "BOUNDED_OFFICIAL_AUTHORITY_DOCUMENTS_ACQUIRED_NOT_ANALYSED"
    assert set(manifest["documents"]) == set(DOCUMENTS)
    for key, spec in DOCUMENTS.items():
        assert (tmp_path / spec["output_name"]).read_bytes().startswith(b"%PDF-")
        assert manifest["documents"][key]["requested_url"] == spec["url"]
    guard = manifest["guardrails"]
    assert guard["fixed_document_set_only"] is True
    assert guard["pdf_text_extracted"] is False
    assert guard["code_tables_extracted"] is False
    assert guard["code_translation_performed"] is False
    assert guard["version_compatibility_established"] is False
    assert guard["geological_interpretation_performed"] is False
    assert guard["admission_decision_performed"] is False


def test_rejects_redirect_to_nonofficial_host(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return _pdf("x"), {"content-type": "application/pdf"}, "https://example.org/report.pdf"

    with pytest.raises(ValueError, match="escaped official"):
        acquire_geotop_authority_documents(tmp_path, get_transport=transport)


def test_rejects_non_pdf_payload(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>not pdf</html>", {"content-type": "text/html"}, url

    with pytest.raises(ValueError, match="PDF signature"):
        acquire_geotop_authority_documents(tmp_path, get_transport=transport)


def test_rejects_non_pdf_content_type(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return _pdf("x"), {"content-type": "application/octet-stream"}, url

    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_authority_documents(tmp_path, get_transport=transport)


def test_config_guardrail_is_bounded() -> None:
    cfg = GeoTopAuthorityDocumentConfig()
    assert cfg.max_document_bytes == 30 * 1024 * 1024
    assert cfg.timeout_s == 90
    assert len(DOCUMENTS) == 3
