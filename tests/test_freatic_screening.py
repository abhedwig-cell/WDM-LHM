import numpy as np
import pandas as pd

from wdm_lhm.freatic_screening import (
    FreaticScreeningConfig,
    freatic_prescreen,
    vertical_head_pair_evidence,
    freatic_admission,
)


def _obs(station_id, start="2020-01-01", periods=900, head=7.0, series_class="fully_assessed"):
    dates = pd.date_range(start, periods=periods, freq="D")
    values = head + 0.25 * np.sin(np.arange(periods) / 40.0)
    return pd.DataFrame({
        "station_id": station_id,
        "date": dates,
        "obs_head_mnap": values,
        "series_class": series_class,
    })


def test_prescreen_shallow_candidate_and_deep_review():
    stations = pd.DataFrame([
        {"station_id":"S1", "gmw_bro_id":"G1", "tube_number":1, "gld_bro_id":"L1", "ground_level_mnap":8.0,
         "screen_top_position_mnap":6.5, "screen_bottom_position_mnap":5.5, "tube_status":"gebruiksklaar", "tube_in_use":"ja"},
        {"station_id":"S2", "gmw_bro_id":"G2", "tube_number":1, "gld_bro_id":"L2", "ground_level_mnap":8.0,
         "screen_top_position_mnap":-4.0, "screen_bottom_position_mnap":-6.0, "tube_status":"gebruiksklaar", "tube_in_use":"ja"},
    ])
    obs = pd.concat([_obs("S1"), _obs("S2")], ignore_index=True)
    out = freatic_prescreen(stations, obs)
    s1 = out.set_index("station_id").loc["S1"]
    s2 = out.set_index("station_id").loc["S2"]
    assert s1.prescreen_verdict == "CANDIDATE_FREATIC"
    assert not bool(s1.legacy_gd_depth_risk)
    assert s2.prescreen_verdict == "REVIEW_DEEP_OR_AMBIGUOUS"
    assert bool(s2.legacy_gd_depth_risk)
    assert "LEGACY_GD_DEPTH_RISK" in s2.reason_codes


def test_prescreen_missing_geometry_is_insufficient():
    stations = pd.DataFrame([{"station_id":"S1", "gmw_bro_id":"G1", "tube_number":1, "ground_level_mnap":8.0,
                              "screen_top_position_mnap":np.nan, "screen_bottom_position_mnap":5.5}])
    out = freatic_prescreen(stations, _obs("S1"))
    assert out.iloc[0].prescreen_verdict == "INSUFFICIENT_DATA"


def test_prescreen_short_series_not_usable():
    stations = pd.DataFrame([{"station_id":"S1", "gmw_bro_id":"G1", "tube_number":1, "ground_level_mnap":8.0,
                              "screen_top_position_mnap":6.5, "screen_bottom_position_mnap":5.5}])
    cfg = FreaticScreeningConfig(min_observations=100, min_span_days=730)
    out = freatic_prescreen(stations, _obs("S1", periods=50), cfg)
    assert out.iloc[0].prescreen_verdict == "NOT_USABLE_SERIES"


def test_vertical_head_pair_evidence_reports_persistent_difference():
    stations = pd.DataFrame([
        {"station_id":"S1", "gmw_bro_id":"G1", "ground_level_mnap":8.0,
         "screen_top_position_mnap":6.5, "screen_bottom_position_mnap":5.5},
        {"station_id":"S2", "gmw_bro_id":"G1", "ground_level_mnap":8.0,
         "screen_top_position_mnap":2.0, "screen_bottom_position_mnap":1.0},
    ])
    o1 = _obs("S1", periods=100, head=7.0)
    o2 = _obs("S2", periods=100, head=6.75)
    out = vertical_head_pair_evidence(stations, pd.concat([o1, o2], ignore_index=True), min_overlap_days=30)
    assert len(out) == 1
    r = out.iloc[0]
    assert r.vertical_head_evidence_status == "EVIDENCE_AVAILABLE"
    assert abs(r.median_shallow_minus_deep_head_m - 0.25) < 1e-10
    assert r.positive_sign_fraction == 1.0


def test_admission_is_fail_closed_and_uses_positive_evidence():
    pre = pd.DataFrame([
        {"station_id":"A", "prescreen_verdict":"CANDIDATE_FREATIC"},
        {"station_id":"B", "prescreen_verdict":"REVIEW_DEEP_OR_AMBIGUOUS"},
        {"station_id":"C", "prescreen_verdict":"CANDIDATE_FREATIC"},
    ])
    evidence = pd.DataFrame([
        {"station_id":"A", "hydrogeology_evidence":"freatic_unconfined", "vertical_head_assessment":"compatible"},
        {"station_id":"B", "hydrogeology_evidence":"confined_or_separated"},
    ])
    out = freatic_admission(pre, evidence).set_index("station_id")
    assert out.loc["A", "admission_verdict"] == "ADMISSIBLE_FREATIC"
    assert out.loc["B", "admission_verdict"] == "NOT_ADMISSIBLE_FREATIC"
    assert out.loc["C", "admission_verdict"] == "REVIEW_REQUIRED"
