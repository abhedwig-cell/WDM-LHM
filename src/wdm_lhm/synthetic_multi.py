from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from .synthetic import make_synthetic


def make_multiwell_demo(outdir: str | Path, n_stations: int = 5) -> dict[str, Path]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    base = make_synthetic(seed=2026)
    dates = pd.to_datetime(base["date"])

    cells = pd.DataFrame({
        "cell_id": [f"C{i}" for i in range(9)],
        "x_rd": np.tile([100000.0, 100250.0, 100500.0], 3),
        "y_rd": np.repeat([450000.0, 450250.0, 450500.0], 3),
        "ground_level_mnap": [10.0, 10.1, 10.2, 10.15, 10.25, 10.35, 10.3, 10.4, 10.5],
    })
    stations = pd.DataFrame({
        "station_id": [f"S{i+1}" for i in range(n_stations)],
        "x_rd": [100020, 100235, 100490, 100110, 100420][:n_stations],
        "y_rd": [450030, 450265, 450470, 450410, 450120][:n_stations],
        "ground_level_mnap": [10.02, 10.24, 10.48, 10.28, 10.18][:n_stations],
        "drain_level_mnap": [9.25, 9.40, 9.65, 9.45, 9.35][:n_stations],
    })

    forcing = base[["date", "precip_mm", "et_mm"]].copy()
    model_depth = base["model_head_mnap"]
    ref_gl = float(base["ground_level_mnap"].iloc[0])
    depth_m = ref_gl - model_depth.to_numpy(float)
    mts_rows = []
    for j, cell in cells.iterrows():
        spatial_offset = (j - 4) * 0.015
        head = float(cell.ground_level_mnap) - depth_m + spatial_offset
        local_drain_level = float(cell.ground_level_mnap) - 0.80
        drain_flux = np.maximum(head - local_drain_level, 0.0) * 7.5
        river_flux = np.maximum(head - (local_drain_level + 0.10), 0.0) * 2.5
        recharge = forcing["precip_mm"].to_numpy(float) - forcing["et_mm"].to_numpy(float)
        mts_rows.append(pd.DataFrame({
            "date": dates,
            "cell_id": cell.cell_id,
            "model_head_mnap": head,
            "drain_flux_mm_d": drain_flux,
            "river_flux_mm_d": river_flux,
            "recharge_mm_d": recharge,
        }))
    mts = pd.concat(mts_rows, ignore_index=True)

    obs_rows = []
    base_obs_depth_m = ref_gl - base["obs_head_mnap"].to_numpy(float)
    rng = np.random.default_rng(9)
    for i, st in stations.iterrows():
        local_shift = (i - 2) * 0.02
        local_scale = 1.0 + 0.05 * (i - 2)
        depth = base_obs_depth_m.mean() + local_scale * (base_obs_depth_m - base_obs_depth_m.mean()) + local_shift
        head = float(st.ground_level_mnap) - depth + rng.normal(0, 0.005, len(depth))
        obs_rows.append(pd.DataFrame({"date": dates, "station_id": st.station_id, "obs_head_mnap": head}))
    obs = pd.concat(obs_rows, ignore_index=True)

    paths = {
        "observations": out / "observations.csv",
        "model_timeseries": out / "model_timeseries.csv",
        "stations": out / "stations.csv",
        "cells": out / "cells.csv",
        "forcing": out / "forcing.csv",
    }
    obs.to_csv(paths["observations"], index=False)
    mts.to_csv(paths["model_timeseries"], index=False)
    stations.to_csv(paths["stations"], index=False)
    cells.to_csv(paths["cells"], index=False)
    forcing.to_csv(paths["forcing"], index=False)
    return paths
