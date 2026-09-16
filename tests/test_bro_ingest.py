import json

from wdm_lhm.bro_ingest import BROIngestConfig, ingest_bro_groundwater, parse_gld_compact_csv


def _feature(fid, props, lon=5.67, lat=51.97):
    return {"type":"Feature", "id":fid, "geometry":{"type":"Point","coordinates":[lon,lat]}, "properties":props}


def test_parse_gld_compact_csv_dutch_columns():
    payload = ("tijdstip meting;waterstand;status kwaliteitscontrole\n"
               "2024-01-01T12:00:00+01:00;7,123;goedgekeurd\n"
               "2024-01-02T12:00:00+01:00;7,111;goedgekeurd\n").encode()
    out = parse_gld_compact_csv(payload, gld_bro_id="GLD000000000999", station_id="GMWX_T1", series_class="fully_assessed")
    assert len(out) == 2
    assert abs(out.iloc[0].obs_head_mnap - 7.123) < 1e-9
    assert out.iloc[0].station_id == "GMWX_T1"


def test_ingest_relational_join_cache_and_lineage(tmp_path):
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
    gld_csv=("tijdstip meting;waterstand\n2024-01-01T12:00:00+01:00;7,10\n2024-01-02T12:00:00+01:00;7,00\n").encode()

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
    st=r['stations'].iloc[0]
    assert st['used_in_wdm'] == 'unknown'
    assert st['used_in_lhm_calibration'] == 'unknown'
    assert st['ground_level_mnap'] == 8.4
    assert 100000 < st['x_rd'] < 300000
    n=len(calls)
    ingest_bro_groundwater(tmp_path, cfg, transport=transport)
    assert len(calls) == n
