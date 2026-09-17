from pathlib import Path

import pytest

from wdm_lhm.geotop_metadata import (
    GEOTOP_DATASET_URL,
    GeoTopMetadataConfig,
    acquire_geotop_metadata,
    parse_dds,
    validate_das,
)


DDS = """Dataset {
    Float64 x[x = 3];
    Float64 y[y = 2];
    Float64 z[z = 4];
    Byte strat[z = 4][y = 2][x = 3];
    Byte lithok[z = 4][y = 2][x = 3];
} geotop;
"""

DAS = """Attributes {
  x {
    String units "m";
  }
  y {
    String units "m";
  }
  z {
    String units "m";
  }
  strat {
    String long_name "stratigraphy";
  }
}
"""


def test_parse_dds_inventory():
    parsed = parse_dds(DDS)
    assert parsed["dimensions"] == {"x": 3, "y": 2, "z": 4}
    assert parsed["variables"]["strat"]["dimensions"][0] == {"name": "z", "size": 4}


def test_inconsistent_dimension_fails_closed():
    bad = DDS.replace("Byte strat[z = 4][y = 2][x = 3];", "Byte strat[z = 5][y = 2][x = 3];")
    with pytest.raises(ValueError, match="inconsistent DDS dimension"):
        parse_dds(bad)


def test_missing_coordinate_fails_closed():
    with pytest.raises(ValueError, match="coordinate variable missing"):
        parse_dds(DDS.replace("    Float64 z[z = 4];\n", ""))


def test_das_requires_attribute_sections():
    with pytest.raises(ValueError):
        validate_das("Attributes {\n}\n")


def test_metadata_probe_issues_only_dds_das(tmp_path: Path):
    calls = []

    def transport(url, headers, timeout_s, max_bytes):
        calls.append(url)
        if url.endswith(".dds"):
            return DDS.encode(), {"content-type": "text/plain"}, url
        if url.endswith(".das"):
            return DAS.encode(), {"content-type": "text/plain"}, url
        raise AssertionError(url)

    manifest = acquire_geotop_metadata(tmp_path, get_transport=transport)
    assert calls == [f"{GEOTOP_DATASET_URL}.dds", f"{GEOTOP_DATASET_URL}.das"]
    assert manifest["guardrails"]["data_requests_issued"] is False
    assert manifest["guardrails"]["constraint_expression_issued"] is False
    assert manifest["guardrails"]["voxel_values_read"] is False
    assert manifest["expected_variable_presence"]["strat"] is True
    assert manifest["expected_variable_presence"]["lithok"] is True


def test_redirect_drift_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        payload = DDS.encode() if url.endswith(".dds") else DAS.encode()
        return payload, {"content-type": "text/plain"}, "https://example.org/geotop.nc.dds"

    with pytest.raises(ValueError, match="redirect"):
        acquire_geotop_metadata(tmp_path, get_transport=transport)


def test_dataset_path_drift_fails_closed(tmp_path: Path):
    cfg = GeoTopMetadataConfig(dataset_url="https://www.dinodata.nl/opendap/hyrax/GeoTOP/other.nc")
    with pytest.raises(ValueError, match="path drift"):
        acquire_geotop_metadata(tmp_path, config=cfg)
