from pathlib import Path

import pytest

from wdm_lhm.geotop_coordinate_acquisition import (
    COORDINATE_VARIABLES,
    GEOTOP_DATASET_URL,
    GeoTopCoordinateAcquisitionConfig,
    acquire_geotop_coordinate_axes,
    build_coordinate_ascii_url,
)


def test_fixed_coordinate_url():
    assert build_coordinate_ascii_url() == f"{GEOTOP_DATASET_URL}.ascii?x,y,z"


def test_variable_set_cannot_be_broadened():
    with pytest.raises(ValueError, match="exactly"):
        build_coordinate_ascii_url(variables=("x", "y", "z", "strat"))


def test_dataset_cannot_drift():
    with pytest.raises(ValueError, match="pinned"):
        build_coordinate_ascii_url(dataset_url="https://www.dinodata.nl/opendap/hyrax/GeoTOP/other.nc")


def test_raw_acquisition_preserves_no_interpretation_boundary(tmp_path: Path):
    payload = b"Dataset: geotop.nc\nx, 0, 100\ny, 0, 100\nz, -1, -0.5\n"
    requested = f"{GEOTOP_DATASET_URL}.ascii?x,y,z"

    def transport(url, headers, timeout_s, max_bytes):
        assert url == requested
        return payload, {"content-type": "text/plain; charset=UTF-8"}, url

    manifest = acquire_geotop_coordinate_axes(tmp_path, get_transport=transport)
    assert manifest["request"]["variables"] == list(COORDINATE_VARIABLES)
    assert manifest["state"] == "RAW_COORDINATE_AXES_ACQUIRED_NOT_PARSED"
    assert manifest["guardrails"]["coordinate_values_requested"] is True
    assert manifest["guardrails"]["categorical_voxel_values_requested"] is False
    assert manifest["guardrails"]["strat_requested"] is False
    assert manifest["guardrails"]["lithok_requested"] is False
    assert manifest["guardrails"]["coordinate_axes_parsed"] is False
    assert manifest["guardrails"]["point_to_cell_mapping_performed"] is False
    assert manifest["guardrails"]["hydraulic_interpretation_performed"] is False
    assert (tmp_path / "geotop_coordinate_axes.ascii.txt").read_bytes() == payload


def test_query_drift_fails_closed(tmp_path: Path):
    payload = b"x, 0\ny, 0\nz, 0\n"

    def transport(url, headers, timeout_s, max_bytes):
        return payload, {"content-type": "text/plain"}, f"{GEOTOP_DATASET_URL}.ascii?x,y,z,strat"

    with pytest.raises(ValueError, match="query drift"):
        acquire_geotop_coordinate_axes(tmp_path, get_transport=transport)


def test_host_drift_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        return b"x, 0", {"content-type": "text/plain"}, "https://example.org/geotop.nc.ascii?x,y,z"

    with pytest.raises(ValueError, match="fixed host"):
        acquire_geotop_coordinate_axes(tmp_path, get_transport=transport)


def test_unexpected_content_type_fails_closed(tmp_path: Path):
    requested = f"{GEOTOP_DATASET_URL}.ascii?x,y,z"

    def transport(url, headers, timeout_s, max_bytes):
        return b"x, 0", {"content-type": "application/octet-stream"}, requested

    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_coordinate_axes(tmp_path, get_transport=transport)


def test_empty_response_fails_closed(tmp_path: Path):
    requested = f"{GEOTOP_DATASET_URL}.ascii?x,y,z"

    def transport(url, headers, timeout_s, max_bytes):
        return b"", {"content-type": "text/plain"}, requested

    with pytest.raises(ValueError, match="empty"):
        acquire_geotop_coordinate_axes(tmp_path, get_transport=transport)


def test_guardrail_rejects_transport_payload_over_limit(tmp_path: Path):
    cfg = GeoTopCoordinateAcquisitionConfig(max_response_bytes=3)
    requested = f"{GEOTOP_DATASET_URL}.ascii?x,y,z"

    def transport(url, headers, timeout_s, max_bytes):
        return b"1234", {"content-type": "text/plain"}, requested

    with pytest.raises(ValueError, match="guardrail"):
        acquire_geotop_coordinate_axes(tmp_path, config=cfg, get_transport=transport)
