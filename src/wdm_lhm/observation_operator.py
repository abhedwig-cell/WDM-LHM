from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OperatorConfig:
    method: str = "nearest"
    k: int = 4
    power: float = 2.0
    max_distance_m: float = 500.0
    max_ground_level_delta_m: float = 1.0

    def as_dict(self) -> dict:
        return asdict(self)


STATION_REQUIRED = {"station_id", "x_rd", "y_rd", "ground_level_mnap"}
CELL_REQUIRED = {"cell_id", "x_rd", "y_rd", "ground_level_mnap"}


def _validate_metadata(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{name} missing required columns: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise ValueError(f"{name} contains missing values in required columns")


def _idw_weights(dist: np.ndarray, power: float) -> np.ndarray:
    if np.any(dist == 0.0):
        w = np.zeros_like(dist, dtype=float)
        w[np.argmin(dist)] = 1.0
        return w
    raw = 1.0 / np.power(dist, power)
    return raw / raw.sum()


def build_observation_operator(
    stations: pd.DataFrame,
    cells: pd.DataFrame,
    config: OperatorConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build an explicit spatial operator from monitoring points to model cells.

    Supported methods are `nearest` and `idw`. The returned long table contains
    one or more weighted model cells per station. The station summary contains
    transparent mapping diagnostics and a PASS/FAIL QC status.
    """
    config = config or OperatorConfig()
    if config.method not in {"nearest", "idw"}:
        raise ValueError("Operator method must be 'nearest' or 'idw'.")
    if config.k < 1:
        raise ValueError("k must be >= 1")
    if config.power <= 0:
        raise ValueError("power must be > 0")

    _validate_metadata(stations, STATION_REQUIRED, "stations")
    _validate_metadata(cells, CELL_REQUIRED, "cells")
    if stations["station_id"].duplicated().any():
        raise ValueError("station_id must be unique in stations metadata")
    if cells["cell_id"].duplicated().any():
        raise ValueError("cell_id must be unique in cells metadata")

    cell_xy = cells[["x_rd", "y_rd"]].to_numpy(float)
    rows: list[dict] = []
    summaries: list[dict] = []

    for st in stations.itertuples(index=False):
        dx = cell_xy[:, 0] - float(st.x_rd)
        dy = cell_xy[:, 1] - float(st.y_rd)
        dist = np.sqrt(dx * dx + dy * dy)
        order = np.argsort(dist)
        nsel = 1 if config.method == "nearest" else min(config.k, len(cells))
        sel = order[:nsel]
        selected_dist = dist[sel]
        weights = np.array([1.0]) if nsel == 1 else _idw_weights(selected_dist, config.power)

        selected = cells.iloc[sel].copy()
        weighted_gl = float(np.sum(weights * selected["ground_level_mnap"].to_numpy(float)))
        gl_delta = weighted_gl - float(st.ground_level_mnap)
        nearest_distance = float(selected_dist.min())
        qc_distance = nearest_distance <= config.max_distance_m
        qc_ground = abs(gl_delta) <= config.max_ground_level_delta_m
        qc_status = "PASS" if qc_distance and qc_ground else "FAIL"

        for (_, cell), d, w in zip(selected.iterrows(), selected_dist, weights):
            rows.append({
                "station_id": st.station_id,
                "cell_id": cell["cell_id"],
                "weight": float(w),
                "distance_m": float(d),
                "station_x_rd": float(st.x_rd),
                "station_y_rd": float(st.y_rd),
                "cell_x_rd": float(cell["x_rd"]),
                "cell_y_rd": float(cell["y_rd"]),
                "station_ground_level_mnap": float(st.ground_level_mnap),
                "cell_ground_level_mnap": float(cell["ground_level_mnap"]),
                "operator_method": config.method,
            })

        summaries.append({
            "station_id": st.station_id,
            "operator_method": config.method,
            "n_cells": int(nsel),
            "nearest_distance_m": nearest_distance,
            "weighted_cell_ground_level_mnap": weighted_gl,
            "station_ground_level_mnap": float(st.ground_level_mnap),
            "ground_level_delta_m": gl_delta,
            "qc_distance": bool(qc_distance),
            "qc_ground_level": bool(qc_ground),
            "mapping_qc": qc_status,
        })

    return pd.DataFrame(rows), pd.DataFrame(summaries)


def apply_observation_operator(model_timeseries: pd.DataFrame, operator: pd.DataFrame) -> pd.DataFrame:
    """Apply a weighted cell operator to transient model variables.

    `model_head_mnap` is required. Additional numeric model variables, such as
    drainage or river fluxes, are propagated through the same spatial operator.
    This keeps state and diagnostic fluxes on identical spatial support.
    """
    required = {"date", "cell_id", "model_head_mnap"}
    missing = required - set(model_timeseries.columns)
    if missing:
        raise ValueError(f"model_timeseries missing required columns: {sorted(missing)}")
    op_required = {"station_id", "cell_id", "weight"}
    missing_op = op_required - set(operator.columns)
    if missing_op:
        raise ValueError(f"operator missing required columns: {sorted(missing_op)}")

    mts = model_timeseries.copy()
    mts["date"] = pd.to_datetime(mts["date"], errors="raise")
    value_cols = [c for c in mts.columns if c not in {"date", "cell_id"} and pd.api.types.is_numeric_dtype(mts[c])]
    if "model_head_mnap" not in value_cols:
        raise ValueError("model_head_mnap must be numeric")
    merged = operator[["station_id", "cell_id", "weight"]].merge(mts, on="cell_id", how="left", validate="many_to_many")
    if merged["model_head_mnap"].isna().any():
        missing_cells = sorted(set(merged.loc[merged["model_head_mnap"].isna(), "cell_id"].astype(str)))
        raise ValueError(f"Missing model heads for operator cells, e.g. {missing_cells[:5]}")
    weighted_cols = []
    rename = {}
    for col in value_cols:
        wcol = f"__weighted__{col}"
        merged[wcol] = merged["weight"] * merged[col]
        weighted_cols.append(wcol)
        rename[wcol] = col
    out = merged.groupby(["station_id", "date"], as_index=False)[weighted_cols].sum(min_count=1)
    return out.rename(columns=rename)
