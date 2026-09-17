import json
import pandas as pd

from wdm_lhm.bro_ingest import BROIngestConfig, ingest_bro_groundwater, parse_gld_compact_csv


def _feature(fid, props, lon=5.67, lat=51.97):
    return {"type":"Feature", "id":fid, "geometry":{"type":"Point","coordinates":[lon,lat]}, "properties":props}


def test_parse_gld_compact_csv_dutch_columns_preserves_assessment_status():
    payload = ("tijdstip meting;waterstand;status kwaliteitscontrole\n"
               "2024-01-01T12:00:00+01:00;7,123;goedgekeurd\n"
               "2024-01-02T12:00:00+01:00;7,111;afgekeurd\n").encode()
    out = parse_gld_compact_csv(payload, gld_bro_id="GLD000000000999", station_id="GMWX_T1", series_class="fully_assessed")
    assert len(out) == 2
    assert abs(out.iloc[0].obs_head_mnap - 7.123) < 1e-9
    assert out.iloc[0].station_id == "GMWX_T1"
    assert list(out["assessment_status_raw"]) == ["goedgekeurd", "afgekeurd"]
    assert list(out["assessment_status"]) == ["goedgekeurd", "afgekeurd"]


def test_parse_gld_compact_csv_live_headerless_format_preserves_all_statuses():
    payload = (
        ',,,,,\n'
        '"1975-02-28T12:00:00+01:00","6.550","goedgekeurd",,,"discontinu"\n'
        '"1975-03-14T12:00:00+01:00","6.660","afgekeurd",,,"discontinu"\n'
        '"1975-03-28T12:00:00+01:00","6.700","onbeslist",,,"discontinu"\n'
        ',,,,,\n'
    ).encode()
    out = parse_gld_compact_csv(
        payload, gld_bro_id="GLD000000002815", station_id="GMW000000004104_T1", series_class="fully_assessed"
    )
    assert len(out) == 3
    assert out.iloc[0]["obs_head_mnap"] == 6.55
    assert out.iloc[1]["obs_head_mnap"] == 6.66
    assert out.iloc[0]["date"] == pd.Timestamp("1975-02-28 12:00:00")
    assert list(out["assessment_status"]) == ["goedgekeurd", "afgekeurd", "onbeslist"]


def test_parse_gld_compact_csv_does_not_assume_missing_status_is_approved():
    payload = (
        "tijdstip meting;waterstand\n"
        "2024-01-01T12:00:00+01:00;7,10\n"
        "2024-01-02T12:00:00+01:00;7,00\n"
    ).encode()
    out = parse_gld_compact_csv(
        payload, gld_bro_id="GLD000000000999", station_id="GMWX_T1", series_class="fully_assessed"
    )
    assert len(out) == 2
    assert out["assessment_status"].isna().all()
    assert out["assessment_status_raw"].isna().all()


def test_ingest_relational_join_cache_lineage_and_assessment_counts(tmp_path):
    gmw_fc = {"type":"FeatureCollection","features":[_feature("gw1", {
        "gm_gmw_pk": 10, "bro_id":"GMW000000000123", "ground_level_position":8.4,
        "quality_regime":"IMBRO", "nitg_code":"39A-TEST"
    })], "links":[]}
    tube_fc = {"type":"FeatureCollection","features":[_feature("t1", {
        "gm_gmw_monitoringtube_pk": 20, "gm_gmw_fk":10, "gmw_bro_id":"GMW000000000123",
        "tube_number":1, "tube_in_use":"ja", "tube_status":"gebruiksklaar",
        "screen_top_position":6.4, "screen_bottom_position":5.4
    })], "links":[]}
    gld_fc = {"type":"FeatureCollection","features":[_feature("gld1", {
        "gm_gld_pk":30, "gm_gmw_monitoringtube_fk":20, "bro_id":"GLD000000000999",
        "quality_regime":"IMBRO", "number_of_observations":100,
        "research_first_date":"2020-01-01", "research_last_date":"2024-01-01",
        "series_fully_assessed_csv_url":"https://example.test/gld999.csv",
        "series_preliminary_csv_url":"https://example.test/gld999-pre.csv"
    })], "links":[]}
    gld_csv=("tijdstip meting;waterstand;status kwaliteitscontrole\n"
             "2024-01-01T12:00:00+01:00;7,10;goedgekeurd\n"
             "2024-01-02T12:00:00+01:00;7,00;afgekeurd\n").encode()

    calls=[]
    def transport(url, headers, timeout):
        calls.append(url)
        if '/gm_gmw/items?' in url: return json.dumps(gmw_fc).encode()
        if '/gm_gmw_monitoringtube/items?' in url: return json.dumps(tube_fc).encode()
        if '/gm_gld/items?' in url: return json.dumps(gld_fc).encode()
        if url == 'https://example.test/gld999.csv': return gld_csv
        raise AssertionError(url)

    cfg=BROIngestConfig((5.6,51.9,5.8,52.1), min_observations=30, min_span_days=365)
    r=ingest_bro_groundwater(tmp_path, cfg, transport=transport)
    assert r['manifest']['counts']['stations'] == 1
    assert len(r['observations']) == 2
    assert r['manifest']['assessment_status_counts'] == {'goedgekeurd': 1, 'afgekeurd': 1}
    assert list(r['observations']['assessment_status']) == ['goedgekeurd', 'afgekeurd']
    st=r['stations'].iloc[0]
    assert st['used_in_wdm'] == 'unknown'
    assert st['used_in_lhm_calibration'] == 'unknown'
    assert st['ground_level_mnap'] == 8.4
    assert 100000 < st['x_rd'] < 300000
    n=len(calls)
    ingest_bro_groundwater(tmp_path, cfg, transport=transport)
    assert len(calls) == n
