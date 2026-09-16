from __future__ import annotations

import numpy as np
import pandas as pd


def paired_metrics(obs: pd.Series, model: pd.Series) -> dict[str, float]:
    df = pd.concat({"obs": obs, "model": model}, axis=1).dropna()
    if df.empty:
        return {k: np.nan for k in ["n", "bias", "mae", "rmse", "corr", "std_ratio"]}
    residual = df["model"] - df["obs"]
    obs_std = float(df["obs"].std(ddof=1))
    mod_std = float(df["model"].std(ddof=1))
    return {
        "n": int(len(df)),
        "bias": float(residual.mean()),
        "mae": float(residual.abs().mean()),
        "rmse": float(np.sqrt(np.mean(residual.to_numpy() ** 2))),
        "corr": float(df["obs"].corr(df["model"])) if len(df) > 1 else np.nan,
        "std_ratio": mod_std / obs_std if obs_std > 0 else np.nan,
    }
