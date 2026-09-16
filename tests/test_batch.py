from wdm_lhm.synthetic_multi import make_multiwell_demo
from wdm_lhm.batch import run_batch
from wdm_lhm.observation_operator import OperatorConfig


def test_multiwell_demo_runs(tmp_path):
    paths = make_multiwell_demo(tmp_path / "inputs", n_stations=3)
    result = run_batch(
        paths["observations"], paths["model_timeseries"], paths["stations"], paths["cells"], paths["forcing"],
        tmp_path / "results", OperatorConfig(method="idw", k=4, max_distance_m=400, max_ground_level_delta_m=0.5)
    )
    assert result["manifest"]["n_stations"] == 3
    assert result["manifest"]["n_analysed"] == 3
    assert (tmp_path / "results" / "station_summary.csv").exists()
    assert (tmp_path / "results" / "observation_operator.csv").exists()
