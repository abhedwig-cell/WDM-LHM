import json
import pandas as pd

from wdm_lhm.bro_ingest import BROIngestConfig, ingest_bro_groundwater
from wdm_lhm.freatic_screening import FreaticScreeningConfig, freatic_prescreen


def _feature(fid, props, lon=5.67, lat=51.97):
    return {"type": "Feature", "id": fid, "geometry": {"type": "Point", "coordinates": [lon, lat]}, "properties": props}


def test_catalog_observation_entities_are_not_measurement_points(tmp_path):
    """Two GLD Observatie entities may contain a long series of time-value pairs."""
    gmw_fc = {"type": "FeatureCollection", "features": [_feature("gw1", {
        "gm_gmw_pk": 10, "bro_id": "GMW000000000123", "ground_level_position": 8.0,
        "quality_regime": "IMBRO",
    })], "links": []}
    tube_fc = {"type": "FeatureCollection", "features": [_feature("t1", {
        "gm_gmw_monitoringtube_pk": 20, "gm_gmw_fk": 10, "gmw_bro_id": "GMW000000000123",
        "tube_number": 1, "tube_in_use": "ja", "tube_status": "gebruiksklaar",
        "screen_top_position": 6.5, "screen_bottom_position": 5.5,
    })], "links": []}
    gld_fc = {"type": "FeatureCollection", "features": [_feature("gld1", {
        "gm_gld_pk": 30, "gm_gmw_monitoringtube_fk": 20, "bro_id": "GLD000000000999",
        "quality_regime": "IMBRO",
        # This is a count of Observatie entities / periods, not time-value pairs.
        "number_of_observations": 2,
        "research_first_date": "2020-01-01", "research_last_date": "2022-12-31",
        "series_fully_assessed_csv_url": "https://example.test/gld999.csv",
    })], "links": []}

    dates = pd.date_range("2020-01-01", "2022-12-31", periods=120)
    lines = ["tijdstip meting;waterstand"]
    lines += [f"{d.isoformat()}+01:00;{7.0 + 0.1 * ((i % 10) / 10):.3f}" for i, d in enumerate(dates)]
    gld_csv = ("\n".join(lines) + "\n").encode()

    def transport(url, headers, timeout):
        if "/gm_gmw/items?" in url:
            return json.dumps(gmw_fc).encode()
        if "/gm_gmw_monitoringtube/items?" in url:
            return json.dumps(tube_fc).encode()
        if "/gm_gld/items?" in url:
            return json.dumps(gld_fc).encode()
        if url == "https://example.test/gld999.csv":
            return gld_csv
        raise AssertionError(url)

    ingest = ingest_bro_groundwater(
        tmp_path / "bro",
        BROIngestConfig((5.6, 51.9, 5.8, 52.1), min_observations=1, min_span_days=730),
        transport=transport,
    )
    assert len(ingest["observations"]) == 120

    screen = freatic_prescreen(
        ingest["stations"],
        ingest["observations"],
        FreaticScreeningConfig(min_observations=100, min_span_days=730),
    )
    assert screen.iloc[0]["n_observations"] == 120
    assert screen.iloc[0]["prescreen_verdict"] == "CANDIDATE_FREATIC"
