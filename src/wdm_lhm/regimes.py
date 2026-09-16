from __future__ import annotations

import numpy as np
import pandas as pd


def residual_regime_table(obs_depth_cm: pd.Series, model_depth_cm: pd.Series, q: int = 5) -> pd.DataFrame:
    """Summarize model-minus-observation residual by simulated depth regime."""
    df = pd.concat({"obs": obs_depth_cm, "model": model_depth_cm}, axis=1).dropna()
    if df.empty:
        return pd.DataFrame()
    df["residual_cm"] = df["model"] - df["obs"]
    try:
        df["depth_regime"] = pd.qcut(df["model"], q=q, duplicates="drop")
    except ValueError:
        df["depth_regime"] = "all"
    grouped = df.groupby("depth_regime", observed=True)
    out = grouped.agg(
        n=("residual_cm", "size"),
        model_depth_mean_cm=("model", "mean"),
        residual_mean_cm=("residual_cm", "mean"),
        residual_rmse_cm=("residual_cm", lambda x: float(np.sqrt(np.mean(np.asarray(x) ** 2)))),
    ).reset_index()
    out["depth_regime"] = out["depth_regime"].astype(str)
    return out


def direction_regime_table(obs_depth_cm: pd.Series, model_depth_cm: pd.Series) -> pd.DataFrame:
    """Compare residuals while groundwater is rising versus falling.

    With depth positive downward, decreasing depth means the water table is rising.
    """
    df = pd.concat({"obs": obs_depth_cm, "model": model_depth_cm}, axis=1).dropna()
    df["d_model"] = df["model"].diff()
    df["residual_cm"] = df["model"] - df["obs"]
    df["direction"] = np.where(df["d_model"] < 0, "rising", np.where(df["d_model"] > 0, "falling", "stable"))
    return df.groupby("direction", observed=True).agg(
        n=("residual_cm", "size"),
        residual_mean_cm=("residual_cm", "mean"),
        residual_std_cm=("residual_cm", "std"),
    ).reset_index()
