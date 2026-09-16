import pandas as pd
import numpy as np
from wdm_lhm.observation_operator import OperatorConfig, build_observation_operator, apply_observation_operator


def test_nearest_operator_and_application():
    stations = pd.DataFrame({
        "station_id": ["S1"], "x_rd": [10.0], "y_rd": [0.0], "ground_level_mnap": [5.0]
    })
    cells = pd.DataFrame({
        "cell_id": ["A", "B"], "x_rd": [0.0, 100.0], "y_rd": [0.0, 0.0],
        "ground_level_mnap": [5.0, 5.2]
    })
    op, summary = build_observation_operator(stations, cells, OperatorConfig(method="nearest", max_distance_m=50))
    assert op.iloc[0]["cell_id"] == "A"
    assert summary.iloc[0]["mapping_qc"] == "PASS"

    mts = pd.DataFrame({"date": ["2020-01-01", "2020-01-02"], "cell_id": ["A", "A"], "model_head_mnap": [4.0, 4.1]})
    out = apply_observation_operator(mts, op)
    assert np.allclose(out["model_head_mnap"], [4.0, 4.1])


def test_idw_weights_sum_to_one():
    stations = pd.DataFrame({
        "station_id": ["S1"], "x_rd": [50.0], "y_rd": [0.0], "ground_level_mnap": [5.0]
    })
    cells = pd.DataFrame({
        "cell_id": ["A", "B"], "x_rd": [0.0, 100.0], "y_rd": [0.0, 0.0],
        "ground_level_mnap": [5.0, 5.0]
    })
    op, _ = build_observation_operator(stations, cells, OperatorConfig(method="idw", k=2))
    assert np.isclose(op["weight"].sum(), 1.0)
    assert np.allclose(sorted(op["weight"]), [0.5, 0.5])
