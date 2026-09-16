from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

from wdm_lhm.regis_recursive_inventory import build_recursive_regis_inventory


def _zip_bytes(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, payload in files.items():
            zf.writestr(name, payload)
    return buf.getvalue()


def _three_level_delivery(path: Path) -> None:
    terminal = _zip_bytes(
        {
            "grids/top_layer.asc": b"1 2 3\n",
            "grids/base_layer.asc": b"4 5 6\n",
            "README.txt": b"synthetic model inventory only\n",
        }
    )
    wrapper = _zip_bytes(
        {
            "release_report.pdf": b"not-a-real-pdf",
            "REGIS_release.zip": terminal,
        }
    )
    outer = _zip_bytes(
        {
            "MetaData.xml": b"<metadata/>",
            "Model_HGM.zip": wrapper,
        }
    )
    path.write_bytes(outer)


def test_recursive_inventory_reaches_terminal_archive_without_extracting_leaf_members(tmp_path: Path) -> None:
    source = tmp_path / "brohgm.zip"
    output = tmp_path / "evidence"
    _three_level_delivery(source)

    manifest = build_recursive_regis_inventory(source, output, max_depth=6)

    assert manifest["status"] == "RECURSIVE_INVENTORY_ONLY_NO_NONZIP_MEMBERS_EXTRACTED"
    assert manifest["inventory"]["container_count"] == 3
    assert manifest["inventory"]["zip_members_materialized"] == 2
    assert manifest["inventory"]["max_archive_depth_reached"] == 2
    assert manifest["inventory"]["terminal_archive_count"] == 1
    assert manifest["inventory"]["depth_limited_zip_member_count"] == 0
    assert manifest["inventory"]["leaf_extensions"][".asc"] == 2
    assert manifest["guardrails"]["nonzip_members_extracted"] == 0

    output_names = sorted(p.name for p in output.iterdir())
    assert output_names == [
        "regis_recursive_containers.csv",
        "regis_recursive_inventory.csv",
        "regis_recursive_inventory_manifest.json",
    ]
    assert not any(p.suffix.lower() in {".asc", ".zip"} for p in output.iterdir())

    with (output / "regis_recursive_inventory.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    chains = {row["archive_chain"] for row in rows}
    assert "brohgm.zip!/Model_HGM.zip!/REGIS_release.zip" in chains
    assert any(row["member_name"] == "grids/top_layer.asc" for row in rows)

    persisted = json.loads((output / "regis_recursive_inventory_manifest.json").read_text())
    assert persisted == manifest


def test_recursive_inventory_reports_depth_limit_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "brohgm.zip"
    output = tmp_path / "evidence"
    _three_level_delivery(source)

    manifest = build_recursive_regis_inventory(source, output, max_depth=1)

    assert manifest["inventory"]["container_count"] == 2
    assert manifest["inventory"]["max_archive_depth_reached"] == 1
    assert manifest["inventory"]["depth_limited_zip_member_count"] == 1
    assert manifest["inventory"]["terminal_archive_count"] == 0
    assert manifest["guardrails"]["nonzip_members_extracted"] == 0
