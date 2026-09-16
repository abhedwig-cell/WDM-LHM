from pathlib import Path
import pandas as pd

from wdm_lhm.admission import admit_bundle
from wdm_lhm.synthetic_multi import make_multiwell_demo


def _bundle(tmp_path: Path):
    paths = make_multiwell_demo(tmp_path / "inputs", n_stations=3)
    stations = pd.read_csv(paths["stations"])
    stations["used_in_wdm"] = ["yes", "no", "unknown"]
    stations["used_in_lhm_calibration"] = ["no", "yes", "no"]
    stations["heldout_group"] = ["train", "development", "heldout"]
    stations["metadata_source"] = ["test"] * 3
    stations.to_csv(paths["stations"], index=False)

    flux_meta = tmp_path / "inputs" / "flux_metadata.csv"
    pd.DataFrame([
        {"variable": "drain_flux_mm_d", "unit": "mm/d", "sign_convention": "positive_out", "process": "drainage", "source": "synthetic", "temporal_support": "daily"},
        {"variable": "river_flux_mm_d", "unit": "mm/d", "sign_convention": "positive_out", "process": "river", "source": "synthetic", "temporal_support": "daily"},
        {"variable": "recharge_mm_d", "unit": "mm/d", "sign_convention": "positive_in", "process": "recharge", "source": "synthetic", "temporal_support": "daily"},
    ]).to_csv(flux_meta, index=False)

    model = pd.read_csv(paths["model_timeseries"])
    run_meta = tmp_path / "inputs" / "run_metadata.csv"
    pd.DataFrame([{
        "model_run_id": "SYNTH-01",
        "model_version": "test",
        "source": "unit-test",
        "run_period_start": model["date"].min(),
        "run_period_end": model["date"].max(),
    }]).to_csv(run_meta, index=False)
    return paths, flux_meta, run_meta


def test_valid_bundle_passes_with_heldout_and_flux_semantics(tmp_path):
    paths, flux_meta, run_meta = _bundle(tmp_path)
    result = admit_bundle(
        paths["observations"], paths["model_timeseries"], paths["stations"], paths["cells"], paths["forcing"],
        tmp_path / "admission", flux_metadata_path=flux_meta, run_metadata_path=run_meta,
    )
    assert result["verdict"] == "PASS"
    assert result["report"]["n_heldout"] == 1
    assert result["report"]["n_response_model_eligible"] == 3


def test_missing_heldout_station_blocks_bundle(tmp_path):
    paths, flux_meta, run_meta = _bundle(tmp_path)
    stations = pd.read_csv(paths["stations"])
    stations["heldout_group"] = "train"
    stations.to_csv(paths["stations"], index=False)
    result = admit_bundle(
        paths["observations"], paths["model_timeseries"], paths["stations"], paths["cells"], paths["forcing"],
        tmp_path / "admission", flux_metadata_path=flux_meta, run_metadata_path=run_meta,
    )
    assert result["verdict"] == "BLOCKED"
    row = result["checks"].loc[result["checks"]["check_id"] == "heldout_available"].iloc[0]
    assert row["status"] == "FAIL"


def test_undocumented_process_flux_blocks_bundle(tmp_path):
    paths, flux_meta, run_meta = _bundle(tmp_path)
    meta = pd.read_csv(flux_meta)
    meta = meta[meta["variable"] != "river_flux_mm_d"]
    meta.to_csv(flux_meta, index=False)
    result = admit_bundle(
        paths["observations"], paths["model_timeseries"], paths["stations"], paths["cells"], paths["forcing"],
        tmp_path / "admission", flux_metadata_path=flux_meta, run_metadata_path=run_meta,
    )
    assert result["verdict"] == "BLOCKED"
    row = result["checks"].loc[result["checks"]["check_id"] == "flux_semantics"].iloc[0]
    assert row["status"] == "FAIL"
