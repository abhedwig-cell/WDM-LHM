from pathlib import Path
import hashlib

import pytest

import wdm_lhm.geotop_authority_text_extraction as mod


def _install_fake_sources(monkeypatch, source: Path) -> dict[str, dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}
    for key in ("v16_supplement", "v161_small_release", "general_report"):
        name = f"{key}.pdf"
        payload = b"%PDF-1.7\n" + key.encode("utf-8") + b"\n%%EOF\n"
        (source / name).write_bytes(payload)
        specs[key] = {"input_name": name, "sha256": hashlib.sha256(payload).hexdigest()}
    monkeypatch.setattr(mod, "EXPECTED_DOCUMENTS", specs)
    return specs


def test_extracts_verified_text_with_page_index(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    out = tmp_path / "out"
    source.mkdir()
    _install_fake_sources(monkeypatch, source)

    def extractor(pdf_path: Path, text_path: Path) -> None:
        text_path.write_text(
            "GeoTOP 1.6.1 strat 1000 lithoklasse 3\fSecond page code 5120 lithok 7\f",
            encoding="utf-8",
        )

    manifest = mod.extract_geotop_authority_text(
        source,
        out,
        extractor=extractor,
        extractor_identity="fake-pdftotext 1.0",
    )

    assert manifest["state"] == "QUALIFIED_SOURCE_TEXT_EXTRACTED_NOT_SEMANTICALLY_ADJUDICATED"
    assert manifest["extractor_identity"] == "fake-pdftotext 1.0"
    for key, record in manifest["documents"].items():
        assert record["page_count"] == 2
        assert len(record["page_index"]) == 2
        assert record["page_index"][0]["page"] == 1
        assert record["page_index"][1]["page"] == 2
        assert record["page_index"][0]["observed_code_occurrences"]["strat"]["1000"] == 1
        assert record["page_index"][1]["observed_code_occurrences"]["strat"]["5120"] == 1
        assert record["page_index"][0]["observed_code_occurrences"]["lithok"]["3"] == 1
        assert record["page_index"][1]["observed_code_occurrences"]["lithok"]["7"] == 1
        assert (out / record["text_file"]).exists()
    guard = manifest["guardrails"]
    assert guard["exact_gate_3a_hashes_required"] is True
    assert guard["page_index_preserved"] is True
    assert guard["code_translation_performed"] is False
    assert guard["version_compatibility_established"] is False
    assert guard["geological_interpretation_performed"] is False
    assert guard["hydraulic_interpretation_performed"] is False
    assert guard["admission_decision_performed"] is False


def test_rejects_source_hash_drift(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    out = tmp_path / "out"
    source.mkdir()
    specs = _install_fake_sources(monkeypatch, source)
    specs["v16_supplement"]["sha256"] = "0" * 64

    with pytest.raises(ValueError, match="SHA drift"):
        mod.extract_geotop_authority_text(
            source,
            out,
            extractor=lambda pdf, text: text.write_text("unused", encoding="utf-8"),
            extractor_identity="fake",
        )


def test_rejects_empty_extraction(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    out = tmp_path / "out"
    source.mkdir()
    _install_fake_sources(monkeypatch, source)

    def extractor(pdf_path: Path, text_path: Path) -> None:
        text_path.write_bytes(b"")

    with pytest.raises(ValueError, match="empty output"):
        mod.extract_geotop_authority_text(
            source,
            out,
            extractor=extractor,
            extractor_identity="fake",
        )


def test_single_page_text_remains_one_page(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source"
    out = tmp_path / "out"
    source.mkdir()
    _install_fake_sources(monkeypatch, source)

    def extractor(pdf_path: Path, text_path: Path) -> None:
        text_path.write_text("GeoTOP code 3030", encoding="utf-8")

    manifest = mod.extract_geotop_authority_text(
        source,
        out,
        extractor=extractor,
        extractor_identity="fake",
    )
    assert all(record["page_count"] == 1 for record in manifest["documents"].values())
