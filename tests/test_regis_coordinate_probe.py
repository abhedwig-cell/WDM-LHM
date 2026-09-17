from pathlib import Path

import pytest

from wdm_lhm.regis_coordinate_probe import (
    COORDINATE_VARIABLES,
    REGIS_DATASET_URL,
    RegisCoordinateProbeConfig,
    acquire_regis_coordinate_evidence,
    build_coordinate_ascii_url,
)


def test_coordinate_url_is_fixed_and_contains_only_coordinate_variables():
    url = build_coordinate_ascii_url()
    assert url == (
        "https://www.dinodata.nl/opendap/REGIS/REGIS.nc.ascii?"
        "x,y,x_bounds,y_bounds,layer"
    )
    assert all(name in url for name in COORDINATE_VARIABLES)
    for forbidden in ("top", "bottom", "hgv", "kD", "kh", "kv", "sdh", "sdv", "freatisch"):
        assert forbidden not in url


def test_coordinate_url_rejects_dataset_or_variable_drift():
    with pytest.raises(ValueError, match="pinned"):
        build_coordinate_ascii_url("https://www.dinodata.nl/opendap/REGIS/other.nc")
    with pytest.raises(ValueError, match="exactly"):
        build_coordinate_ascii_url(REGIS_DATASET_URL, ("x", "y"))


def test_coordinate_probe_retains_raw_response_without_interpretation(tmp_path: Path):
    payload = b"x, 3\n50, 150, 250\ny, 2\n624950, 624850\nlayer, 2\n\"AA\", \"BB\"\n"
    requested: list[str] = []

    def transport(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        requested.append(url)
        return (
            payload,
            {"content-type": "text/plain; charset=UTF-8", "content-length": str(len(payload))},
            url,
        )

    manifest = acquire_regis_coordinate_evidence(tmp_path, get_transport=transport)

    assert requested == [build_coordinate_ascii_url()]
    assert manifest["request"]["variables"] == list(COORDINATE_VARIABLES)
    assert manifest["response"]["bytes"] == len(payload)
    assert manifest["guardrails"]["coordinate_values_requested"] is True
    assert manifest["guardrails"]["hydrogeological_model_values_requested"] is False
    assert manifest["guardrails"]["point_to_cell_mapping_performed"] is False
    assert (tmp_path / "regis_coordinate_response.ascii.txt").read_bytes() == payload
    assert (tmp_path / "regis_coordinate_manifest.json").is_file()


def test_coordinate_probe_fails_closed_on_oversized_or_wrong_endpoint(tmp_path: Path):
    def too_large(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        return b"x" * 11, {"content-type": "text/plain"}, url

    with pytest.raises(ValueError, match="exceeds guardrail"):
        acquire_regis_coordinate_evidence(
            tmp_path / "large",
            RegisCoordinateProbeConfig(max_response_bytes=10),
            get_transport=too_large,
        )

    def wrong_endpoint(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        return b"x, 1\n50\n", {"content-type": "text/plain"}, "https://example.invalid/data.ascii"

    with pytest.raises(ValueError, match="Unexpected coordinate response endpoint"):
        acquire_regis_coordinate_evidence(tmp_path / "redirect", get_transport=wrong_endpoint)
