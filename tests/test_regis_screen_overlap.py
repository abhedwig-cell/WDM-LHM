from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from wdm_lhm.regis_screen_overlap import derive_screen_intervals, qualify_screen_overlap


def _write_parsed(tmp_path: Path, columns: dict) -> tuple[Path, str]:
    payload = {
        "columns": columns,
        "guardrails": {"screen_to_unit_mapping_performed": False},
    }
    raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    path = tmp_path / "parsed.json"
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def _column(x: str, y: str, layers: list[dict]) -> dict:
    return {"x": x, "y": y, "layers": layers}


def test_screen_intervals_use_bro_ground_level_exactly():
    screens = derive_screen_intervals()
    assert screens["GMW000000004074"]["tube1"]["screen_top_m_nap"] == "5.72"
    assert screens["GMW000000004074"]["tube1"]["screen_bottom_m_nap"] == "2.72"
    assert screens["GMW000000004074"]["tube2"]["screen_top_m_nap"] == "-3.16"
    assert screens["GMW000000004074"]["tube2"]["screen_bottom_m_nap"] == "-3.66"
    assert screens["GMW000000004104"]["tube1"]["screen_top_m_nap"] == "-2.21"
    assert screens["GMW000000004104"]["tube2"]["screen_bottom_m_nap"] == "-28.17"


def test_geometry_overlap_preserves_boundary_sensitivity_and_surface_diagnostic(tmp_path: Path):
    columns = {
        "4074_nominal": _column("170300", "440700", [
            {"layer": "mv", "top": "8.15", "bottom": None},
            {"layer": "NUBXz3", "top": "7.67", "bottom": "5.03"},
            {"layer": "NUBXz4", "top": "5.03", "bottom": "3.96"},
            {"layer": "NUgsc", "top": "3.96", "bottom": "-21.17"},
        ]),
        "4074_west_boundary_sensitivity": _column("170200", "440700", [
            {"layer": "mv", "top": "7.77", "bottom": None},
            {"layer": "NUgsc", "top": "5.94", "bottom": "-20.88"},
        ]),
        "4104_nominal": _column("169600", "441500", [
            {"layer": "mv", "top": "11.15", "bottom": None},
            {"layer": "NUgsc", "top": "9.98", "bottom": "-24.7"},
            {"layer": "NUPZ-WAz1", "top": "-24.7", "bottom": "-31.31"},
        ]),
    }
    parsed, digest = _write_parsed(tmp_path, columns)
    out = tmp_path / "overlap.json"
    result = qualify_screen_overlap(parsed, out, expected_parsed_sha256=digest)

    t1 = result["results"]["4074_nominal"]["screens"]["tube1"]
    assert t1["layer_sequence"] == ["NUBXz3", "NUBXz4", "NUgsc"]
    assert [item["overlap_m"] for item in t1["overlaps"]] == ["0.69", "1.07", "1.24"]
    assert t1["coverage_complete"] is True

    west = result["results"]["4074_west_boundary_sensitivity"]["screens"]["tube1"]
    assert west["layer_sequence"] == ["NUgsc"]
    assert west["overlaps"][0]["overlap_m"] == "3.00"

    comparison = result["comparisons"]["4074_boundary_sensitivity"]["tubes"]
    assert comparison["tube1"]["same_layer_sequence"] is False
    assert comparison["tube2"]["same_layer_sequence"] is True

    assert result["results"]["4074_nominal"]["surface_diagnostic"] == {
        "regis_mv_m_nap": "8.15",
        "bro_ground_m_nap": "7.93",
        "regis_minus_bro_ground_m": "0.22",
        "used_for_screen_elevation": False,
    }
    assert result["results"]["4104_nominal"]["surface_diagnostic"]["regis_minus_bro_ground_m"] == "1.34"
    assert result["guardrails"]["admission_decision_performed"] is False


def test_overlap_fails_closed_on_hash_drift(tmp_path: Path):
    columns = {
        "4074_nominal": _column("170300", "440700", []),
        "4074_west_boundary_sensitivity": _column("170200", "440700", []),
        "4104_nominal": _column("169600", "441500", []),
    }
    parsed, _ = _write_parsed(tmp_path, columns)
    with pytest.raises(ValueError, match="SHA-256 drift"):
        qualify_screen_overlap(parsed, tmp_path / "out.json", expected_parsed_sha256="0" * 64)


def test_overlap_rejects_double_counted_layer_geometry(tmp_path: Path):
    columns = {
        "4074_nominal": _column("170300", "440700", [
            {"layer": "mv", "top": "8.15", "bottom": None},
            {"layer": "A", "top": "6", "bottom": "3"},
            {"layer": "B", "top": "5", "bottom": "2"},
        ]),
        "4074_west_boundary_sensitivity": _column("170200", "440700", [
            {"layer": "mv", "top": "7.77", "bottom": None},
        ]),
        "4104_nominal": _column("169600", "441500", [
            {"layer": "mv", "top": "11.15", "bottom": None},
        ]),
    }
    parsed, digest = _write_parsed(tmp_path, columns)
    with pytest.raises(ValueError, match="double-count"):
        qualify_screen_overlap(parsed, tmp_path / "out.json", expected_parsed_sha256=digest)
