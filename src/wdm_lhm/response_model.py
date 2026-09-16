from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar


@dataclass(frozen=True)
class LinearReservoirFit:
    offset: float
    gain: float
    memory_a: float
    tau_days: float
    rmse: float
    n: int

    def as_dict(self) -> dict:
        return asdict(self)


def _reservoir_state(recharge: np.ndarray, a: float) -> np.ndarray:
    state = np.empty_like(recharge, dtype=float)
    x = 0.0
    for i, r in enumerate(recharge):
        x = a * x + r
        state[i] = x
    return state


def fit_linear_reservoir(target: pd.Series, precipitation_mm: pd.Series, et_mm: pd.Series) -> LinearReservoirFit:
    """Fit the same simple response model to an observed or simulated series.

    Model:
        recharge_t = precipitation_t - et_t
        x_t = a*x_(t-1) + recharge_t
        target_t = offset + gain*x_t + error_t

    `a` captures memory. tau_days = -1/log(a). For groundwater depth positive
    downward, gain is commonly negative because recharge raises the water table.

    This is deliberately a diagnostic model, not a replacement groundwater model.
    """
    df = pd.concat({"y": target, "p": precipitation_mm, "et": et_mm}, axis=1).dropna()
    if len(df) < 30:
        raise ValueError("At least 30 complete daily observations are required for response fitting.")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DatetimeIndex required.")
    diffs = df.index.to_series().diff().dropna().dt.total_seconds() / 86400.0
    if not np.allclose(diffs, 1.0):
        raise ValueError("TS01 response fitting currently requires a regular daily time step.")

    y = df["y"].to_numpy(float)
    r = (df["p"] - df["et"]).to_numpy(float)

    def fit_given_a(a: float) -> tuple[float, float, float]:
        x = _reservoir_state(r, a)
        X = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ coef
        mse = float(np.mean((y - pred) ** 2))
        return mse, float(coef[0]), float(coef[1])

    result = minimize_scalar(lambda a: fit_given_a(float(a))[0], bounds=(0.001, 0.9995), method="bounded")
    a = float(result.x)
    mse, offset, gain = fit_given_a(a)
    tau = -1.0 / math.log(a)
    return LinearReservoirFit(offset=offset, gain=gain, memory_a=a, tau_days=tau, rmse=math.sqrt(mse), n=len(df))
