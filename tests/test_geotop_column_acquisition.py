from pathlib import Path
from urllib.parse import quote

import pytest

from wdm_lhm.geotop_column_acquisition import (
    COLUMN_CONSTRAINT_EXPRESSION,
    COLUMN_VARIABLES,
    GEOTOP_DATASET_URL,
    QUALIFIED_X_INDEX,
    QUALIFIED_Y_INDEX,
    QUALIFIED_Z_START,
    QUALIFIED_Z_STOP,
    GeoTopColumnAcquisitionConfig,
    acquire_geotop_single_column,
    build_column_ascii_url,
)


def test_fixed_single_column_url():
    assert build_column_ascii_url() == f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"


def test_variable_set_cannot_be_broadened():
    with pytest.raises(ValueError, match="exactly"):
        build_column_ascii_url(variables=("strat", "lithok", "kans_1"))


def test_horizontal_indices_cannot_drift():
    with pytest.raises(ValueError, match="qualified x/y"):
        build_column_ascii_url(x_index=QUALIFIED_X_INDEX + 1)
    with pytest.raises(ValueError, match="qualified x/y"):
        build_column_ascii_url(y_index=QUALIFIED_Y_INDEX - 1)


def test_z_range_cannot_be_narrowed_or_broadened():
    with pytest.raises(ValueError, match="complete qualified z-index"):
        build_column_ascii_url(z_start=QUALIFIED_Z_START + 1)
    with pytest.raises(ValueError, match="complete qualified z-index"):
        build_column_ascii_url(z_stop=QUALIFIED_Z_STOP - 1)


def test_dataset_cannot_drift():
    with pytest.raises(ValueError, match="pinned"):
        build_column_ascii_url(dataset_url="https://www.dinodata.nl/opendap/hyrax/GeoTOP/other.nc")


def test_raw_acquisition_preserves_no_interpretation_boundary(tmp_path: Path):
    payload = b"Dataset: geotop.nc\nstrat.strat, 1, 2\nlithok.lithok, 5, 6\n"
    requested = f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    def transport(url, headers, timeout_s, max_bytes):
        assert url == requested
        return payload, {"content-type": "text/plain; charset=UTF-8"}, url

    manifest = acquire_geotop_single_column(tmp_path, get_transport=transport)
    assert manifest["request"]["variables"] == list(COLUMN_VARIABLES)
    assert manifest["request"]["x_index_zero_based"] == QUALIFIED_X_INDEX
    assert manifest["request"]["y_index_zero_based"] == QUALIFIED_Y_INDEX
    assert manifest["request"]["z_index_range_inclusive"] == [QUALIFIED_Z_START, QUALIFIED_Z_STOP]
    assert manifest["state"] == "RAW_SINGLE_COLUMN_ACQUIRED_NOT_PARSED"
    guardrails = manifest["guardrails"]
    assert guardrails["single_horizontal_column_only"] is True
    assert guardrails["categorical_voxel_values_requested"] is True
    assert guardrails["strat_requested"] is True
    assert guardrails["lithok_requested"] is True
    assert guardrails["probability_grids_requested"] is False
    assert guardrails["uncertainty_grids_requested"] is False
    assert guardrails["neighbour_columns_requested"] is False
    assert guardrails["response_parsed"] is False
    assert guardrails["class_codes_interpreted"] is False
    assert guardrails["screen_correlation_performed"] is False
    assert guardrails["hydraulic_interpretation_performed"] is False
    assert guardrails["admission_decision_performed"] is False
    assert (tmp_path / "geotop_single_column.ascii.txt").read_bytes() == payload


def test_percent_encoded_final_query_is_accepted(tmp_path: Path):
    payload = b"Dataset: geotop.nc\nraw\n"
    encoded_query = quote(COLUMN_CONSTRAINT_EXPRESSION, safe=",:")

    def transport(url, headers, timeout_s, max_bytes):
        return payload, {"content-type": "text/plain"}, f"{GEOTOP_DATASET_URL}.ascii?{encoded_query}"

    manifest = acquire_geotop_single_column(tmp_path, get_transport=transport)
    assert manifest["response"]["bytes"] == len(payload)


def test_query_drift_fails_closed(tmp_path: Path):
    payload = b"raw"

    def transport(url, headers, timeout_s, max_bytes):
        return payload, {"content-type": "text/plain"}, f"{GEOTOP_DATASET_URL}.ascii?strat[1587:1:1587][1092:1:1092][0:1:312]"

    with pytest.raises(ValueError, match="query drift"):
        acquire_geotop_single_column(tmp_path, get_transport=transport)


def test_host_drift_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        return b"raw", {"content-type": "text/plain"}, f"https://example.org/geotop.nc.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    with pytest.raises(ValueError, match="fixed host"):
        acquire_geotop_single_column(tmp_path, get_transport=transport)


def test_unexpected_content_type_fails_closed(tmp_path: Path):
    requested = f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    def transport(url, headers, timeout_s, max_bytes):
        return b"raw", {"content-type": "application/octet-stream"}, requested

    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_single_column(tmp_path, get_transport=transport)


def test_dap_error_document_fails_closed(tmp_path: Path):
    requested = f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    def transport(url, headers, timeout_s, max_bytes):
        return b"Error { code = 400; }", {"content-type": "text/plain"}, requested

    with pytest.raises(ValueError, match="DAP error"):
        acquire_geotop_single_column(tmp_path, get_transport=transport)


def test_empty_response_fails_closed(tmp_path: Path):
    requested = f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    def transport(url, headers, timeout_s, max_bytes):
        return b"", {"content-type": "text/plain"}, requested

    with pytest.raises(ValueError, match="empty"):
        acquire_geotop_single_column(tmp_path, get_transport=transport)


def test_guardrail_rejects_transport_payload_over_limit(tmp_path: Path):
    cfg = GeoTopColumnAcquisitionConfig(max_response_bytes=3)
    requested = f"{GEOTOP_DATASET_URL}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"

    def transport(url, headers, timeout_s, max_bytes):
        return b"1234", {"content-type": "text/plain"}, requested

    with pytest.raises(ValueError, match="guardrail"):
        acquire_geotop_single_column(tmp_path, config=cfg, get_transport=transport)
