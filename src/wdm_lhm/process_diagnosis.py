from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable
import numpy as np
import pandas as pd


DEFAULT_PROCESS_VARIABLES = (
    "drain_flux_mm_d",
    "river_flux_mm_d",
    "surface_water_flux_mm_d",
    "recharge_mm_d",
)


@dataclass(frozen=True)
class ProcessConfig:
    """Configuration for TS04 process diagnostics.

    The analysis is predictive-diagnostic. Added predictive value of a model
    flux is evidence worth investigating, not causal attribution.
    """

    lags_days: tuple[int, ...] = (0, 1, 3, 7, 14, 30)
    cv_folds: int = 5
    min_n: int = 180
    min_fold_n: int = 30
    follow_up_improvement_pct: float = 2.0
    strong_improvement_pct: float = 5.0
    min_sign_stability: float = 0.75

    def as_dict(self) -> dict:
        d = asdict(self)
        d["lags_days"] = list(self.lags_days)
        return d


def _calendar_features(index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    doy = index.dayofyear.to_numpy(float)
    angle = 2.0 * np.pi * doy / 365.25
    return np.sin(angle), np.cos(angle)


def _lag_by_days(series: pd.Series, days: int, target_index: pd.DatetimeIndex) -> pd.Series:
    """Lag a series by calendar days without treating row gaps as days."""
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("TS04 lag diagnostics require a DatetimeIndex")
    if days < 0:
        raise ValueError("lags_days must be >= 0")
    if days == 0:
        return series.reindex(target_index)
    shifted = series.copy()
    shifted.index = shifted.index + pd.to_timedelta(days, unit="D")
    return shifted.reindex(target_index)


def _build_base_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"residual_cm", "model_depth_cm", "d_model_depth_cm"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"process diagnostic frame missing columns: {sorted(missing)}")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError("TS04 requires a DatetimeIndex")
    out = pd.DataFrame(index=frame.index)
    out["residual_cm"] = frame["residual_cm"]
    out["model_depth_cm"] = frame["model_depth_cm"]
    out["d_model_depth_cm"] = frame["d_model_depth_cm"]
    s, c = _calendar_features(frame.index)
    out["season_sin"] = s
    out["season_cos"] = c
    return out


def _standardize_train_test(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.nanmean(x_train, axis=0)
    std = np.nanstd(x_train, axis=0, ddof=0)
    std = np.where(std > 1e-12, std, 1.0)
    return (x_train - mean) / std, (x_test - mean) / std


def _fit_predict_ols(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    xtr, xte = _standardize_train_test(x_train, x_test)
    xtr_i = np.column_stack([np.ones(len(xtr)), xtr])
    xte_i = np.column_stack([np.ones(len(xte)), xte])
    beta, *_ = np.linalg.lstsq(xtr_i, y_train, rcond=None)
    return xte_i @ beta, beta


def _blocked_fold_ids(n: int, folds: int) -> np.ndarray:
    if folds < 2:
        raise ValueError("cv_folds must be >= 2")
    return np.minimum((np.arange(n) * folds // n).astype(int), folds - 1)


def incremental_flux_cv(
    frame: pd.DataFrame,
    variable: str,
    lag_days: int,
    config: ProcessConfig | None = None,
) -> dict:
    """Test if one lagged process variable adds predictive information.

    Baseline: model depth + change in model depth + annual sine/cosine.
    Augmented model: baseline + one lagged model flux.

    All comparisons use the exact same rows and contiguous blocked folds.
    """
    config = config or ProcessConfig()
    result = {
        "variable": variable,
        "lag_days": int(lag_days),
        "n": 0,
        "cv_folds_valid": 0,
        "baseline_rmse_cm": np.nan,
        "augmented_rmse_cm": np.nan,
        "delta_rmse_cm": np.nan,
        "relative_improvement_pct": np.nan,
        "flux_beta_standardized_median": np.nan,
        "flux_beta_positive_fraction": np.nan,
        "sign_stability": np.nan,
        "status": "NOT_QUALIFIED",
        "evidence_label": "NOT_QUALIFIED",
    }
    if variable not in frame.columns:
        result["evidence_label"] = "MISSING_VARIABLE"
        return result

    base = _build_base_frame(frame)
    base["flux"] = _lag_by_days(frame[variable], lag_days, frame.index)
    d = base.dropna().copy()
    result["n"] = int(len(d))
    if len(d) < config.min_n or d["flux"].nunique() < 3:
        return result

    base_cols = ["model_depth_cm", "d_model_depth_cm", "season_sin", "season_cos"]
    aug_cols = base_cols + ["flux"]
    y = d["residual_cm"].to_numpy(float)
    xb = d[base_cols].to_numpy(float)
    xa = d[aug_cols].to_numpy(float)
    fold_ids = _blocked_fold_ids(len(d), config.cv_folds)

    pred_b = np.full(len(d), np.nan)
    pred_a = np.full(len(d), np.nan)
    flux_betas: list[float] = []
    valid_folds = 0
    for fold in range(config.cv_folds):
        test = fold_ids == fold
        train = ~test
        if train.sum() < max(config.min_fold_n * 2, 40) or test.sum() < config.min_fold_n:
            continue
        try:
            pred_b[test], _ = _fit_predict_ols(xb[train], y[train], xb[test])
            pred_a[test], beta = _fit_predict_ols(xa[train], y[train], xa[test])
            flux_betas.append(float(beta[-1]))
            valid_folds += 1
        except np.linalg.LinAlgError:
            continue

    valid = np.isfinite(pred_b) & np.isfinite(pred_a)
    if valid_folds < max(3, config.cv_folds - 1) or valid.sum() < int(0.75 * len(d)):
        return result

    rmse_b = float(np.sqrt(np.mean((y[valid] - pred_b[valid]) ** 2)))
    rmse_a = float(np.sqrt(np.mean((y[valid] - pred_a[valid]) ** 2)))
    delta = rmse_b - rmse_a
    rel = 100.0 * delta / rmse_b if rmse_b > 0 else np.nan
    betas = np.asarray(flux_betas, float)
    positive_fraction = float(np.mean(betas > 0))
    sign_stability = float(max(positive_fraction, 1.0 - positive_fraction))

    evidence = "NO_CLEAR_INCREMENTAL_SIGNAL"
    if np.isfinite(rel) and rel >= config.follow_up_improvement_pct and sign_stability >= config.min_sign_stability:
        evidence = "FOLLOW_UP"
    if np.isfinite(rel) and rel >= config.strong_improvement_pct and sign_stability >= config.min_sign_stability:
        evidence = "STRONG_FOLLOW_UP"

    result.update({
        "cv_folds_valid": int(valid_folds),
        "baseline_rmse_cm": rmse_b,
        "augmented_rmse_cm": rmse_a,
        "delta_rmse_cm": delta,
        "relative_improvement_pct": rel,
        "flux_beta_standardized_median": float(np.median(betas)),
        "flux_beta_positive_fraction": positive_fraction,
        "sign_stability": sign_stability,
        "status": "PASS",
        "evidence_label": evidence,
    })
    return result


def screen_process_variables(
    frame: pd.DataFrame,
    variables: Iterable[str] | None = None,
    config: ProcessConfig | None = None,
) -> pd.DataFrame:
    """Exploratory blocked-CV screening across variables and calendar-day lags.

    Selecting the best lag from this table is itself data-driven. The selected
    lag must be confirmed on held-out stations/periods before a physical claim.
    """
    config = config or ProcessConfig()
    variables = list(variables or DEFAULT_PROCESS_VARIABLES)
    rows: list[dict] = []
    for var in variables:
        if var not in frame.columns:
            rows.append(incremental_flux_cv(frame, var, 0, config))
            continue
        for lag in config.lags_days:
            rows.append(incremental_flux_cv(frame, var, int(lag), config))
    return pd.DataFrame(rows)


def select_exploratory_best(screen: pd.DataFrame) -> pd.DataFrame:
    """Return the best qualified lag per variable for prioritisation only."""
    if screen.empty:
        return pd.DataFrame()
    rows: list[pd.Series] = []
    for var, group in screen.groupby("variable", sort=False):
        q = group[group["status"] == "PASS"].dropna(subset=["augmented_rmse_cm"])
        if q.empty:
            rows.append(group.iloc[0])
        else:
            rows.append(q.sort_values(["augmented_rmse_cm", "lag_days"]).iloc[0])
    return pd.DataFrame(rows).reset_index(drop=True)


def overall_best_process(best: pd.DataFrame) -> dict:
    if best.empty:
        return {}
    q = best[best["status"] == "PASS"].dropna(subset=["augmented_rmse_cm"])
    if q.empty:
        return {}
    row = q.sort_values(["augmented_rmse_cm", "lag_days"]).iloc[0]
    return row.to_dict()
