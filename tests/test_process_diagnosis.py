import numpy as np
import pandas as pd

from wdm_lhm.process_diagnosis import ProcessConfig, screen_process_variables, select_exploratory_best
from wdm_lhm.regime_analysis import prepare_state_frame


def _process_frame(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=n, freq="D")
    t = np.arange(n)
    model_depth = 85.0 + 22.0 * np.sin(t / 47.0) + 4.0 * np.sin(t / 9.0)
    recharge = rng.gamma(1.1, 2.0, n) * (rng.random(n) < 0.28)
    null_flux = rng.normal(0.0, 1.0, n)
    lag = 7
    recharge_lag = np.r_[np.full(lag, np.nan), recharge[:-lag]]
    seasonal = 1.5 * np.sin(2 * np.pi * idx.dayofyear.to_numpy() / 365.25)
    residual = 1.0 + 0.015 * model_depth + seasonal + 0.9 * np.nan_to_num(recharge_lag) + rng.normal(0.0, 0.7, n)
    obs_depth = model_depth - residual
    raw = pd.DataFrame({
        "obs_depth_cm": obs_depth,
        "model_depth_cm": model_depth,
        "recharge_mm_d": recharge,
        "null_flux_mm_d": null_flux,
    }, index=idx)
    return prepare_state_frame(raw)


def test_process_screen_recovers_known_recharge_lag():
    cfg = ProcessConfig(lags_days=(0, 1, 3, 7, 14), min_n=300, cv_folds=5)
    screen = screen_process_variables(_process_frame(), variables=["recharge_mm_d"], config=cfg)
    best = select_exploratory_best(screen).iloc[0]
    assert best["status"] == "PASS"
    assert int(best["lag_days"]) == 7
    assert best["relative_improvement_pct"] > 20.0
    assert best["evidence_label"] == "STRONG_FOLLOW_UP"


def test_process_screen_does_not_promote_independent_noise():
    cfg = ProcessConfig(lags_days=(0, 1, 3, 7, 14), min_n=300, cv_folds=5)
    screen = screen_process_variables(_process_frame(), variables=["null_flux_mm_d"], config=cfg)
    best = select_exploratory_best(screen).iloc[0]
    assert best["status"] == "PASS"
    assert best["relative_improvement_pct"] < 2.0
    assert best["evidence_label"] == "NO_CLEAR_INCREMENTAL_SIGNAL"
