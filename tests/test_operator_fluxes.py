import pandas as pd
from wdm_lhm.observation_operator import apply_observation_operator


def test_operator_propagates_optional_numeric_fluxes():
    op = pd.DataFrame({
        "station_id": ["S1", "S1"],
        "cell_id": ["C1", "C2"],
        "weight": [0.25, 0.75],
    })
    mts = pd.DataFrame({
        "date": ["2020-01-01", "2020-01-01"],
        "cell_id": ["C1", "C2"],
        "model_head_mnap": [10.0, 12.0],
        "drain_flux_mm_d": [2.0, 6.0],
    })
    out = apply_observation_operator(mts, op)
    assert abs(out.loc[0, "model_head_mnap"] - 11.5) < 1e-12
    assert abs(out.loc[0, "drain_flux_mm_d"] - 5.0) < 1e-12
