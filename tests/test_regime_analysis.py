import numpy as np
import pandas as pd

from wdm_lhm.regime_analysis import RegimeConfig, prepare_state_frame, regime_effects, piecewise_diagnostic


def _synthetic_threshold_frame(n=900, seed=4):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    depth = 80 + 35 * np.sin(np.arange(n) / 40.0) + rng.normal(0, 2.0, n)
    residual = 2.0 + 0.02 * depth + 0.18 * np.maximum(0.0, 80.0 - depth) + rng.normal(0, 1.2, n)
    obs_depth = depth - residual
    ground = np.full(n, 10.0)
    drain = np.full(n, 9.2)
    return pd.DataFrame({
        "obs_depth_cm": obs_depth,
        "model_depth_cm": depth,
        "ground_level_mnap": ground,
        "drain_level_mnap": drain,
    }, index=dates)


def test_drain_regime_effect_is_qualified_and_detected():
    cfg = RegimeConfig(min_regime_n=40, bootstrap_n=150, block_days=20)
    state = prepare_state_frame(_synthetic_threshold_frame(), cfg)
    effects = regime_effects(state, cfg)
    row = effects.loc[effects["effect"] == "drain_active_minus_inactive"].iloc[0]
    assert row["status"] == "PASS"
    assert row["effect_a_minus_b_cm"] > 1.0
    assert row["ci_low_cm"] > 0.0


def test_drain_hinge_improves_blocked_cv():
    cfg = RegimeConfig(min_regime_n=40, bootstrap_n=50, cv_folds=5)
    state = prepare_state_frame(_synthetic_threshold_frame(), cfg)
    table = piecewise_diagnostic(state, cfg)
    row = table.loc[table["model"] == "drain_level_hinge"].iloc[0]
    assert row["status"] == "PASS"
    assert row["relative_improvement_pct"] > 5.0
