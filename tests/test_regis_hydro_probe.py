from pathlib import Path

import pytest

from wdm_lhm.regis_hydro_probe import (
    FORBIDDEN_INDEPENDENT_VARIABLES,
    HYDRO_VARIABLES,
    POINT_COLUMNS,
    RegisHydroProbeConfig,
    acquire_regis_hydro_evidence,
    build_hydro_ascii_url,
)


def test_hydro_urls_are_fixed_to_three_cells_and_five_variables():
    for column_id, point in POINT_COLUMNS.items():
        url = build_hydro_ascii_url(column_id)
        for variable in HYDRO_VARIABLES:
            projection = (
                f"{variable}[0:1:131]"
                f"[{point['y_index']}:1:{point['y_index']}]"
                f"[{point['x_index']}:1:{point['x_index']}]"
            )
            assert projection in url
        for forbidden in FORBIDDEN_INDEPENDENT_VARIABLES:
            assert forbidden not in url


def test_hydro_url_rejects_scope_drift():
    with pytest.raises(ValueError, match="Unknown qualified point column"):
        build_hydro_ascii_url("other")
    with pytest.raises(ValueError, match="exactly"):
        build_hydro_ascii_url("4104_nominal", variables=("top", "bottom"))
    with pytest.raises(ValueError, match="pinned"):
        build_hydro_ascii_url(
            "4104_nominal",
            dataset_url="https://www.dinodata.nl/opendap/REGIS/other.nc",
        )


def test_hydro_probe_retains_three_raw_responses_without_interpretation(tmp_path: Path):
    requested: list[str] = []

    def transport(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        requested.append(url)
        payload = ("Dataset: REGIS.nc\ntop[0][0][0], 1\n" + url).encode()
        assert len(payload) <= max_bytes
        return payload, {"content-type": "text/plain", "content-length": str(len(payload))}, url

    manifest = acquire_regis_hydro_evidence(tmp_path, get_transport=transport)

    assert len(requested) == 3
    assert manifest["counts"]["columns"] == 3
    assert {r["column_id"] for r in manifest["responses"]} == set(POINT_COLUMNS)
    assert manifest["guardrails"]["hydrogeological_model_values_requested"] is True
    assert manifest["guardrails"]["freatic_surface_requested"] is False
    assert manifest["guardrails"]["kd_requested"] is False
    assert manifest["guardrails"]["screen_to_unit_mapping_performed"] is False
    assert manifest["guardrails"]["admission_decision_performed"] is False
    for response in manifest["responses"]:
        assert (tmp_path / response["artifact_file"]).is_file()
        assert response["variables"] == list(HYDRO_VARIABLES)


def test_hydro_probe_fails_closed_on_oversized_or_wrong_endpoint(tmp_path: Path):
    def too_large(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        return b"x" * 11, {"content-type": "text/plain"}, url

    with pytest.raises(ValueError, match="exceeds guardrail"):
        acquire_regis_hydro_evidence(
            tmp_path / "large",
            RegisHydroProbeConfig(max_response_bytes_per_column=10),
            get_transport=too_large,
        )

    def wrong_endpoint(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        return b"x", {"content-type": "text/plain"}, "https://example.invalid/data.ascii"

    with pytest.raises(ValueError, match="Unexpected hydro response endpoint"):
        acquire_regis_hydro_evidence(tmp_path / "redirect", get_transport=wrong_endpoint)
