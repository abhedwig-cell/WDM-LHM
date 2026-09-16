from __future__ import annotations

import numpy as np
import pandas as pd


def make_synthetic(seed: int = 42, years: int = 6) -> pd.DataFrame:
    """Create a deterministic synthetic daily dataset with purposeful model structural error."""
    rng = np.random.default_rng(seed)
    n = int(round(365.25 * years))
    dates = pd.date_range("2018-01-01", periods=n, freq="D")
    doy = dates.dayofyear.to_numpy()

    wet_season = 1.8 + 1.2 * np.cos(2 * np.pi * (doy - 20) / 365.25)
    p = rng.gamma(shape=0.8, scale=np.maximum(wet_season, 0.2))
    dry = rng.random(n) < 0.55
    p[dry] = 0.0
    et = np.maximum(0.0, 1.8 + 1.7 * np.sin(2 * np.pi * (doy - 80) / 365.25))
    recharge = p - et

    def state(a: float):
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = a * x[i - 1] + recharge[i]
        return x

    x_obs = state(0.965)
    x_mod = state(0.94)
    ground = np.full(n, 8.50)
    drain = np.full(n, 7.70)

    obs_depth = 85.0 - 0.55 * x_obs + rng.normal(0, 3.0, n)
    model_depth = 95.0 - 0.44 * x_mod
    wet_mask = model_depth < 80.0
    model_depth[wet_mask] = 80.0 + 0.40 * (model_depth[wet_mask] - 80.0)

    obs_head = ground - obs_depth / 100.0
    model_head = ground - model_depth / 100.0
    return pd.DataFrame({
        "date": dates,
        "obs_head_mnap": obs_head,
        "model_head_mnap": model_head,
        "ground_level_mnap": ground,
        "drain_level_mnap": drain,
        "precip_mm": p,
        "et_mm": et,
    })
