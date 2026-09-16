from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GxGResult:
    ghg_cm: float
    gvg_cm: float
    glg_cm: float
    n_hydro_years_ghg_glg: int
    n_calendar_years_gvg: int

    def as_dict(self) -> dict:
        return asdict(self)


def _nearest_value(series: pd.Series, target: pd.Timestamp, tolerance_days: int) -> float | None:
    if series.empty:
        return None
    idx = series.index.get_indexer([target], method="nearest", tolerance=pd.Timedelta(days=tolerance_days))
    if idx[0] < 0:
        return None
    value = series.iloc[idx[0]]
    return None if pd.isna(value) else float(value)


def semimonthly_samples(depth_cm: pd.Series, tolerance_days: int = 3) -> pd.Series:
    """Sample around the 14th and 28th of each month.

    The input must have a DatetimeIndex and depth positive downward.
    """
    s = depth_cm.sort_index().dropna()
    if s.empty:
        return s
    start = pd.Timestamp(s.index.min().year, s.index.min().month, 1)
    end = pd.Timestamp(s.index.max().year, s.index.max().month, 1)
    rows: list[tuple[pd.Timestamp, float]] = []
    for month in pd.date_range(start, end, freq="MS"):
        for day in (14, 28):
            target = month + pd.Timedelta(days=day - 1)
            value = _nearest_value(s, target, tolerance_days)
            if value is not None:
                rows.append((target, value))
    if not rows:
        return pd.Series(dtype=float, name=depth_cm.name)
    return pd.Series(dict(rows), name=depth_cm.name).sort_index()


def _hydrological_year(ts: pd.Timestamp) -> int:
    return ts.year if ts.month >= 4 else ts.year - 1


def calculate_gxg(depth_cm: pd.Series, tolerance_days: int = 3, min_semimonthly_per_hydro_year: int = 20) -> GxGResult:
    """Calculate GHG, GVG and GLG from a groundwater-depth series.

    GHG/GLG follow the classical semi-monthly HG3/LG3 logic per hydrological year
    (1 April through 31 March), then average over valid hydrological years.
    GVG is the annual mean of values near 14 March, 28 March and 14 April,
    then averaged over valid calendar years.

    This function does not claim 30-year climate representativeness unless the input
    actually spans that period. It reports the number of valid years explicitly.
    """
    semi = semimonthly_samples(depth_cm, tolerance_days=tolerance_days)
    ghg_years: list[float] = []
    glg_years: list[float] = []

    if not semi.empty:
        hydro = pd.Series([_hydrological_year(t) for t in semi.index], index=semi.index)
        for _, grp in semi.groupby(hydro):
            vals = grp.dropna().to_numpy(dtype=float)
            if len(vals) >= min_semimonthly_per_hydro_year:
                ghg_years.append(float(np.mean(np.sort(vals)[:3])))
                glg_years.append(float(np.mean(np.sort(vals)[-3:])))

    s = depth_cm.sort_index().dropna()
    gvg_years: list[float] = []
    if not s.empty:
        for year in range(s.index.min().year, s.index.max().year + 1):
            targets = [pd.Timestamp(year, 3, 14), pd.Timestamp(year, 3, 28), pd.Timestamp(year, 4, 14)]
            values = [_nearest_value(s, t, tolerance_days) for t in targets]
            if all(v is not None for v in values):
                gvg_years.append(float(np.mean(values)))

    return GxGResult(
        ghg_cm=float(np.mean(ghg_years)) if ghg_years else np.nan,
        gvg_cm=float(np.mean(gvg_years)) if gvg_years else np.nan,
        glg_cm=float(np.mean(glg_years)) if glg_years else np.nan,
        n_hydro_years_ghg_glg=len(ghg_years),
        n_calendar_years_gvg=len(gvg_years),
    )
