from __future__ import annotations

import binascii
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

import wdm_lhm.regis_document_authority as authority


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in files.items():
            zf.writestr(name, payload)
    return buf.getvalue()


def _synthetic_delivery(path: Path) -> tuple[bytes, bytes, bytes, bytes]:
    pdf = b"%PDF-1.7\nsynthetic REGIS authority\n%%EOF\n"
    terminal = _zip_bytes(
        {
            authority.AUTHORITY_MEMBER: pdf,
            "REGIS II_v02r2s3/img/freatisch.img": b"RASTER-MUST-NOT-BE-OPENED",
            "REGIS II_v02r2s3/basisdata/REF_REGIS_HYD_UNIT.xlsx": b"XLSX-MUST-NOT-BE-OPENED",
        }
    )
    model = _zip_bytes(
        {
            "release_report.pdf": b"other-document-must-not-be-extracted",
            authority.TERMINAL_MEMBER: terminal,
        }
    )
    outer = _zip_bytes(
        {
            "MetaData.xml": b"<metadata/>",
            authority.MODEL_MEMBER: model,
        }
    )
    path.write_bytes(outer)
    return pdf, terminal, model, outer


def test_extracts_only_exact_authority_document(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "brohgm.zip"
    output = tmp_path / "evidence"
    pdf, terminal, model, outer = _synthetic_delivery(source)

    monkeypatch.setattr(authority, "AUTHORITY_DECLARED_SIZE", len(pdf))
    monkeypatch.setattr(authority, "AUTHORITY_CRC32", f"{binascii.crc32(pdf) & 0xFFFFFFFF:08x}")

    manifest = authority.extract_regis_authority_document(
        source,
        output,
        expected_outer_sha256=hashlib.sha256(outer).hexdigest(),
        expected_model_sha256=hashlib.sha256(model).hexdigest(),
        expected_terminal_sha256=hashlib.sha256(terminal).hexdigest(),
        max_document_bytes=1024,
    )

    assert manifest["status"] == "EXACT_REGIS_AUTHORITY_DOCUMENT_EXTRACTED"
    assert manifest["guardrails"]["extracted_nonzip_member_count"] == 1
    assert manifest["guardrails"]["raster_members_opened"] == 0
    assert manifest["guardrails"]["hydrogeological_interpretation_performed"] is False
    assert manifest["guardrails"]["admission_decision_performed"] is False

    names = sorted(p.name for p in output.iterdir())
    assert names == [
        "Toelichting op de bestanden van REGIS II v2.2.3.pdf",
        "regis_authority_document_manifest.json",
    ]
    assert (output / "Toelichting op de bestanden van REGIS II v2.2.3.pdf").read_bytes() == pdf
    assert not any(p.suffix.lower() in {".img", ".xlsx", ".zip"} for p in output.iterdir())

    persisted = json.loads((output / "regis_authority_document_manifest.json").read_text())
    assert persisted == manifest


def test_fails_closed_on_terminal_archive_hash_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "brohgm.zip"
    output = tmp_path / "evidence"
    pdf, _terminal, model, outer = _synthetic_delivery(source)

    monkeypatch.setattr(authority, "AUTHORITY_DECLARED_SIZE", len(pdf))
    monkeypatch.setattr(authority, "AUTHORITY_CRC32", f"{binascii.crc32(pdf) & 0xFFFFFFFF:08x}")

    with pytest.raises(ValueError, match="Terminal archive SHA-256 drift"):
        authority.extract_regis_authority_document(
            source,
            output,
            expected_outer_sha256=hashlib.sha256(outer).hexdigest(),
            expected_model_sha256=hashlib.sha256(model).hexdigest(),
            expected_terminal_sha256="0" * 64,
            max_document_bytes=1024,
        )

    assert not output.exists() or not any(output.iterdir())
