from __future__ import annotations

from pathlib import Path
import pandas as pd
from .conventions import head_to_depth_cm

REQUIRED = {
    "date",
    "obs_head_mnap",
    "model_head_mnap",
    "ground_level_mnap",
    "precip_mm",
    "et_mm",
}


def read_timeseries(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df = df.sort_values("date").set_index("date")
    if df.index.has_duplicates:
        raise ValueError("Duplicate dates are not allowed in TS01 input.")
    df["obs_depth_cm"] = head_to_depth_cm(df["obs_head_mnap"], df["ground_level_mnap"])
    df["model_depth_cm"] = head_to_depth_cm(df["model_head_mnap"], df["ground_level_mnap"])
    if "drain_level_mnap" in df.columns:
        df["model_above_drain_cm"] = (df["model_head_mnap"] - df["drain_level_mnap"]) * 100.0
    return df
