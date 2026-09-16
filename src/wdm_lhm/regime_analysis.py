from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


@dataclass(frozen=True)
class RegimeConfig:
    """Configuration for diagnostic, state-dependent residual analysis.

    The defaults are deliberately conservative and diagnostic. They do not
    define a correction model.
    """

    near_surface_cm: float = 30.0
    min_regime_n: int = 60
    block_days: int = 30
    bootstrap_n: int = 500
    cv_folds: int = 5
    random_seed: int = 2026

    def as_dict(self) -> dict:
        return asdict(self)


def prepare_state_frame(df: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
    config = config or RegimeConfig()
    required = {"obs_depth_cm", "model_depth_cm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"state frame missing columns: {sorted(missing)}")

    out = df.copy()
    out["residual_cm"] = out["model_depth_cm"] - out["obs_depth_cm"]
    out["d_model_depth_cm"] = out["model_depth_cm"].diff()
    out["direction"] = np.where(
        out["d_model_depth_cm"] < 0,
        "rising",
        np.where(out["d_model_depth_cm"] > 0, "falling", "stable"),
    )
    out["near_surface"] = out["model_depth_cm"] <= config.near_surface_cm

    if "ground_level_mnap" in out.columns and "drain_level_mnap" in out.columns:
        out["drain_depth_cm"] = (out["ground_level_mnap"] - out["drain_level_mnap"]) * 100.0
        out["drain_active_proxy"] = out["model_depth_cm"] < out["drain_depth_cm"]
        out["distance_to_drain_cm"] = out["model_depth_cm"] - out["drain_depth_cm"]
    else:
        out["drain_depth_cm"] = np.nan
        out["drain_active_proxy"] = pd.NA
        out["distance_to_drain_cm"] = np.nan

    if isinstance(out.index, pd.DatetimeIndex):
        month = out.index.month
    elif "date" in out.columns:
        month = pd.to_datetime(out["date"]).dt.month
    else:
        month = pd.Series(np.nan, index=out.index)
    season = pd.Series(index=out.index, dtype="object")
    season.loc[pd.Series(month, index=out.index).isin([12, 1, 2])] = "DJF"
    season.loc[pd.Series(month, index=out.index).isin([3, 4, 5])] = "MAM"
    season.loc[pd.Series(month, index=out.index).isin([6, 7, 8])] = "JJA"
    season.loc[pd.Series(month, index=out.index).isin([9, 10, 11])] = "SON"
    out["season"] = season
    return out


def _summarize_groups(frame: pd.DataFrame, group_col: str) -> pd.DataFrame:
    d = frame.dropna(subset=["residual_cm", group_col]).copy()
    if d.empty:
        return pd.DataFrame(columns=[group_col, "n", "residual_mean_cm", "residual_std_cm", "residual_rmse_cm"])
    return (
        d.groupby(group_col, observed=True)
        .agg(
            n=("residual_cm", "size"),
            residual_mean_cm=("residual_cm", "mean"),
            residual_std_cm=("residual_cm", "std"),
            residual_rmse_cm=("residual_cm", lambda x: float(np.sqrt(np.mean(np.asarray(x, float) ** 2)))),
        )
        .reset_index()
    )


def regime_tables(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "drain": _summarize_groups(frame, "drain_active_proxy"),
        "surface": _summarize_groups(frame, "near_surface"),
        "direction": _summarize_groups(frame, "direction"),
        "season": _summarize_groups(frame, "season"),
    }


def _block_bootstrap_indices(n: int, block_len: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        return np.array([], dtype=int)
    block_len = max(1, min(int(block_len), n))
    starts = rng.integers(0, n, size=int(np.ceil(n / block_len)))
    chunks = []
    base = np.arange(block_len)
    for start in starts:
        chunks.append((start + base) % n)
    return np.concatenate(chunks)[:n]


def _binary_effect(
    frame: pd.DataFrame,
    group_col: str,
    group_a,
    group_b,
    config: RegimeConfig,
    effect_name: str,
) -> dict:
    d = frame[["residual_cm", group_col]].dropna().copy()
    a = d[d[group_col] == group_a]["residual_cm"]
    b = d[d[group_col] == group_b]["residual_cm"]
    result = {
        "effect": effect_name,
        "group_a": str(group_a),
        "group_b": str(group_b),
        "n_a": int(len(a)),
        "n_b": int(len(b)),
        "mean_a_cm": float(a.mean()) if len(a) else np.nan,
        "mean_b_cm": float(b.mean()) if len(b) else np.nan,
        "effect_a_minus_b_cm": float(a.mean() - b.mean()) if len(a) and len(b) else np.nan,
        "ci_low_cm": np.nan,
        "ci_high_cm": np.nan,
        "bootstrap_valid": 0,
        "status": "NOT_QUALIFIED",
    }
    if len(a) < config.min_regime_n or len(b) < config.min_regime_n:
        return result

    rng = np.random.default_rng(config.random_seed)
    vals: list[float] = []
    for _ in range(config.bootstrap_n):
        idx = _block_bootstrap_indices(len(d), config.block_days, rng)
        s = d.iloc[idx]
        sa = s[s[group_col] == group_a]["residual_cm"]
        sb = s[s[group_col] == group_b]["residual_cm"]
        if len(sa) >= max(5, config.min_regime_n // 4) and len(sb) >= max(5, config.min_regime_n // 4):
            vals.append(float(sa.mean() - sb.mean()))
    if len(vals) >= max(50, config.bootstrap_n // 4):
        result["ci_low_cm"], result["ci_high_cm"] = [float(x) for x in np.quantile(vals, [0.025, 0.975])]
        result["bootstrap_valid"] = len(vals)
        result["status"] = "PASS"
    return result


def regime_effects(frame: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
    config = config or RegimeConfig()
    rows = []
    if frame["drain_active_proxy"].notna().any():
        rows.append(_binary_effect(frame, "drain_active_proxy", True, False, config, "drain_active_minus_inactive"))
    rows.append(_binary_effect(frame, "near_surface", True, False, config, "near_surface_minus_deeper"))
    rows.append(_binary_effect(frame, "direction", "rising", "falling", config, "rising_minus_falling"))
    return pd.DataFrame(rows)


def _ols_predict(train_x: np.ndarray, train_y: np.ndarray, test_x: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(train_x, train_y, rcond=None)
    return test_x @ beta


def _design(depth: np.ndarray, knot_cm: float | None = None) -> np.ndarray:
    cols = [np.ones_like(depth, dtype=float), depth.astype(float)]
    if knot_cm is not None:
        cols.append(np.maximum(0.0, float(knot_cm) - depth.astype(float)))
    return np.column_stack(cols)


def _blocked_cv_rmse(depth: np.ndarray, residual: np.ndarray, folds: int, knot_cm: float | None) -> float:
    n = len(depth)
    if n < max(50, folds * 10):
        return np.nan
    fold_ids = np.floor(np.arange(n) * folds / n).astype(int)
    preds = np.full(n, np.nan)
    for k in range(folds):
        test = fold_ids == k
        train = ~test
        if train.sum() < 20 or test.sum() == 0:
            continue
        preds[test] = _ols_predict(_design(depth[train], knot_cm), residual[train], _design(depth[test], knot_cm))
    valid = np.isfinite(preds)
    if valid.sum() < max(30, int(0.8 * n)):
        return np.nan
    return float(np.sqrt(np.mean((residual[valid] - preds[valid]) ** 2)))


def piecewise_diagnostic(frame: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
    """Compare linear residual-depth relation to physically motivated hinge models.

    Uses blocked cross-validation. A lower RMSE for the hinge model is evidence
    worth following up, not proof of a physical threshold mechanism.
    """
    config = config or RegimeConfig()
    d = frame[["model_depth_cm", "residual_cm", "drain_depth_cm"]].dropna(subset=["model_depth_cm", "residual_cm"]).copy()
    if d.empty:
        return pd.DataFrame()
    depth = d["model_depth_cm"].to_numpy(float)
    residual = d["residual_cm"].to_numpy(float)
    linear_rmse = _blocked_cv_rmse(depth, residual, config.cv_folds, None)
    rows = [{
        "model": "linear_depth",
        "knot_cm": np.nan,
        "cv_rmse_cm": linear_rmse,
        "delta_rmse_vs_linear_cm": 0.0,
        "relative_improvement_pct": 0.0,
        "status": "PASS" if np.isfinite(linear_rmse) else "NOT_QUALIFIED",
    }]

    candidates: list[tuple[str, float]] = [("near_surface_hinge", config.near_surface_cm)]
    drain_vals = d["drain_depth_cm"].dropna()
    if not drain_vals.empty:
        candidates.append(("drain_level_hinge", float(drain_vals.median())))

    for name, knot in candidates:
        n_shallow = int((depth < knot).sum())
        n_deep = int((depth >= knot).sum())
        if n_shallow < config.min_regime_n or n_deep < config.min_regime_n:
            rows.append({
                "model": name,
                "knot_cm": knot,
                "cv_rmse_cm": np.nan,
                "delta_rmse_vs_linear_cm": np.nan,
                "relative_improvement_pct": np.nan,
                "status": "NOT_QUALIFIED",
                "n_shallow": n_shallow,
                "n_deep": n_deep,
            })
            continue
        rmse = _blocked_cv_rmse(depth, residual, config.cv_folds, knot)
        improvement = linear_rmse - rmse if np.isfinite(linear_rmse) and np.isfinite(rmse) else np.nan
        rel = 100.0 * improvement / linear_rmse if np.isfinite(improvement) and linear_rmse > 0 else np.nan
        rows.append({
            "model": name,
            "knot_cm": knot,
            "cv_rmse_cm": rmse,
            "delta_rmse_vs_linear_cm": improvement,
            "relative_improvement_pct": rel,
            "status": "PASS" if np.isfinite(rmse) else "NOT_QUALIFIED",
            "n_shallow": n_shallow,
            "n_deep": n_deep,
        })
    return pd.DataFrame(rows)


def flux_diagnostics(frame: pd.DataFrame, variables: Iterable[str] | None = None) -> pd.DataFrame:
    variables = list(variables or [
        "drain_flux_mm_d",
        "river_flux_mm_d",
        "surface_water_flux_mm_d",
        "recharge_mm_d",
    ])
    rows: list[dict] = []
    for var in variables:
        if var not in frame.columns:
            continue
        d = frame[["residual_cm", var]].dropna()
        if len(d) < 20 or d[var].nunique() < 3:
            rows.append({"variable": var, "n": len(d), "spearman_rho": np.nan, "p_value_naive": np.nan, "status": "NOT_QUALIFIED"})
            continue
        rho, p = spearmanr(d[var], d["residual_cm"])
        rows.append({
            "variable": var,
            "n": int(len(d)),
            "spearman_rho": float(rho),
            "p_value_naive": float(p),
            "status": "DESCRIPTIVE_ONLY",
        })
    return pd.DataFrame(rows)
