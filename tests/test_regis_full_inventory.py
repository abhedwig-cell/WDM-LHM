from __future__ import annotations

import json
import zipfile
from pathlib import Path

from wdm_lhm.regis_full_inventory import build_regis_model_inventory


def _make_nested_delivery(tmp_path: Path) -> Path:
    inner = tmp_path / "Model_HGMTEST.zip"
    with zipfile.ZipFile(inner, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("layers/aquifer_top.asc", "ncols 1\nnrows 1\n1\n")
        zf.writestr("layers/aquifer_bottom.asc", "ncols 1\nnrows 1\n0\n")
        zf.writestr("metadata/readme.txt", "synthetic")

    outer = tmp_path / "brohgm.zip"
    with zipfile.ZipFile(outer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MetaData_HGMTEST.xml", "<metadata/>")
        zf.write(inner, arcname="Model_HGMTEST.zip")
    inner.unlink()
    return outer


def test_full_inventory_lists_inner_members_without_extracting_them(tmp_path):
    outer = _make_nested_delivery(tmp_path)
    out = tmp_path / "out"

    manifest = build_regis_model_inventory(outer, out)

    assert manifest["status"] == "INVENTORY_ONLY_NO_MODEL_MEMBERS_EXTRACTED"
    assert manifest["inventory"]["file_count"] == 3
    assert manifest["inventory"]["extensions"][".asc"] == 2
    assert manifest["inventory"]["extensions"][".txt"] == 1
    assert manifest["guardrails"]["inner_members_extracted"] == 0
    assert manifest["guardrails"]["interpretation_performed"] is False
    assert manifest["guardrails"]["admission_decision_performed"] is False

    rows = (out / "regis_inner_inventory.csv").read_text(encoding="utf-8")
    assert "layers/aquifer_top.asc" in rows
    assert not (out / "Model_HGMTEST.zip").exists()
    assert not (out / "layers").exists()

    persisted = json.loads((out / "regis_full_inventory_manifest.json").read_text(encoding="utf-8"))
    assert persisted["nested_model_zip"]["member"] == "Model_HGMTEST.zip"


def test_full_inventory_requires_unique_model_member(tmp_path):
    outer = tmp_path / "ambiguous.zip"
    a = tmp_path / "a.zip"
    b = tmp_path / "b.zip"
    for p in (a, b):
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("x.txt", "x")
    with zipfile.ZipFile(outer, "w") as zf:
        zf.write(a, arcname="Model_A.zip")
        zf.write(b, arcname="Model_B.zip")

    try:
        build_regis_model_inventory(outer, tmp_path / "out")
    except ValueError as exc:
        assert "Expected exactly one Model_*.zip member" in str(exc)
    else:
        raise AssertionError("Expected ambiguous model-member selection to fail closed")
