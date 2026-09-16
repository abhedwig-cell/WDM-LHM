from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
import pandas as pd

from .observation_operator import OperatorConfig, build_observation_operator


@dataclass(frozen=True)
class AdmissionConfig:
    min_overlap_days: int = 365
    recommended_overlap_days: int = 1460
    min_daily_complete_days_for_response: int = 180
    min_heldout_stations: int = 1
    forcing_coverage_min: float = 0.98
    max_mapping_distance_m: float = 500.0
    max_ground_level_delta_m: float = 1.0

    def as_dict(self) -> dict:
        return asdict(self)


STATION_REQUIRED = {
    "station_id", "x_rd", "y_rd", "ground_level_mnap",
    "used_in_wdm", "used_in_lhm_calibration", "heldout_group", "metadata_source",
}
OBS_REQUIRED = {"date", "station_id", "obs_head_mnap"}
CELL_REQUIRED = {"cell_id", "x_rd", "y_rd", "ground_level_mnap"}
MODEL_REQUIRED = {"date", "cell_id", "model_head_mnap"}
FORCING_REQUIRED = {"date", "precip_mm", "et_mm"}
FLUX_METADATA_REQUIRED = {"variable", "unit", "sign_convention", "process", "source", "temporal_support"}
RUN_METADATA_REQUIRED = {"model_run_id", "model_version", "source", "run_period_start", "run_period_end"}

LINEAGE_VALUES = {"yes", "no", "unknown"}
HELDOUT_VALUES = {"train", "development", "heldout", "unknown"}


def _read(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p)


def _check_row(checks: list[dict], check_id: str, severity: str, status: str, message: str, details: str = "") -> None:
    checks.append({
        "check_id": check_id,
        "severity": severity,
        "status": status,
        "message": message,
        "details": details,
    })


def _required_columns(df: pd.DataFrame, required: set[str], name: str, checks: list[dict]) -> bool:
    missing = sorted(required - set(df.columns))
    if missing:
        _check_row(checks, f"columns:{name}", "BLOCKER", "FAIL", f"Missing required columns in {name}", ", ".join(missing))
        return False
    _check_row(checks, f"columns:{name}", "BLOCKER", "PASS", f"Required columns present in {name}")
    return True


def _parse_dates(df: pd.DataFrame, name: str, checks: list[dict]) -> pd.DataFrame:
    out = df.copy()
    try:
        out["date"] = pd.to_datetime(out["date"], errors="raise")
        _check_row(checks, f"dates:{name}", "BLOCKER", "PASS", f"Dates parse in {name}")
    except Exception as exc:
        _check_row(checks, f"dates:{name}", "BLOCKER", "FAIL", f"Invalid dates in {name}", str(exc))
    return out


def _run_metadata(path: str | Path | None, checks: list[dict]) -> dict:
    if path is None:
        _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run metadata file is required")
        return {}
    p = Path(path)
    if not p.exists():
        _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run metadata file not found", str(p))
        return {}
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run metadata JSON invalid", str(exc))
            return {}
    else:
        df = pd.read_csv(p)
        if len(df) != 1:
            _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run metadata CSV must contain exactly one row")
            return {}
        data = df.iloc[0].to_dict()
    missing = sorted(RUN_METADATA_REQUIRED - set(data))
    blanks = sorted(k for k in RUN_METADATA_REQUIRED if k in data and (pd.isna(data[k]) or str(data[k]).strip() == ""))
    if missing or blanks:
        _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run metadata incomplete", f"missing={missing}; blank={blanks}")
        return data
    try:
        start = pd.Timestamp(data["run_period_start"])
        end = pd.Timestamp(data["run_period_end"])
        if end < start:
            raise ValueError("run_period_end precedes run_period_start")
    except Exception as exc:
        _check_row(checks, "run_metadata", "BLOCKER", "FAIL", "Run period invalid", str(exc))
        return data
    _check_row(checks, "run_metadata", "BLOCKER", "PASS", "Model run identity and period are explicit")
    return data


def _flux_metadata(model: pd.DataFrame, path: str | Path | None, checks: list[dict]) -> pd.DataFrame:
    process_cols = [c for c in model.columns if c not in {"date", "cell_id", "model_head_mnap"} and pd.api.types.is_numeric_dtype(model[c])]
    if not process_cols:
        _check_row(checks, "flux_metadata", "INFO", "PASS", "No optional numeric process fluxes supplied")
        return pd.DataFrame()
    if path is None or not Path(path).exists():
        _check_row(checks, "flux_metadata", "BLOCKER", "FAIL", "Process fluxes are present but flux metadata is missing", ", ".join(process_cols))
        return pd.DataFrame()
    meta = pd.read_csv(path)
    if not _required_columns(meta, FLUX_METADATA_REQUIRED, "flux_metadata", checks):
        return meta
    documented = set(meta["variable"].astype(str))
    missing = sorted(set(process_cols) - documented)
    target = meta[meta["variable"].astype(str).isin(process_cols)][list(FLUX_METADATA_REQUIRED)].copy()
    incomplete_mask = target.isna().any(axis=1) | target.astype(str).apply(lambda c: c.str.strip().eq("")).any(axis=1)
    n_incomplete = int(incomplete_mask.sum())
    if missing or n_incomplete:
        _check_row(checks, "flux_semantics", "BLOCKER", "FAIL", "Flux semantics incomplete", f"missing variables={missing}; incomplete rows={n_incomplete}")
    else:
        _check_row(checks, "flux_semantics", "BLOCKER", "PASS", "All optional process variables have explicit semantics")
    return meta


def _daily_complete_run(dates: pd.Series | pd.DatetimeIndex) -> int:
    idx = pd.DatetimeIndex(pd.to_datetime(dates)).sort_values().unique()
    if len(idx) == 0:
        return 0
    best = cur = 1
    for delta in np.diff(idx.values).astype("timedelta64[D]").astype(int):
        if delta == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return int(best)


def admit_bundle(
    observations_path: str | Path,
    model_timeseries_path: str | Path,
    stations_path: str | Path,
    cells_path: str | Path,
    forcing_path: str | Path,
    output_dir: str | Path,
    flux_metadata_path: str | Path | None = None,
    run_metadata_path: str | Path | None = None,
    config: AdmissionConfig | None = None,
) -> dict:
    cfg = config or AdmissionConfig()
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []

    obs = _read(observations_path)
    model = _read(model_timeseries_path)
    stations = _read(stations_path)
    cells = _read(cells_path)
    forcing = _read(forcing_path)

    schemas_ok = all([
        _required_columns(obs, OBS_REQUIRED, "observations", checks),
        _required_columns(model, MODEL_REQUIRED, "model_timeseries", checks),
        _required_columns(stations, STATION_REQUIRED, "stations", checks),
        _required_columns(cells, CELL_REQUIRED, "cells", checks),
        _required_columns(forcing, FORCING_REQUIRED, "forcing", checks),
    ])
    if not schemas_ok:
        checks_df = pd.DataFrame(checks)
        checks_df.to_csv(outdir / "admission_checks.csv", index=False)
        report = {"verdict": "BLOCKED", "reason": "schema blockers", "config": cfg.as_dict()}
        (outdir / "admission_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return {"verdict": "BLOCKED", "checks": checks_df, "stations": pd.DataFrame(), "report": report}

    obs = _parse_dates(obs, "observations", checks)
    model = _parse_dates(model, "model_timeseries", checks)
    forcing = _parse_dates(forcing, "forcing", checks)

    for name, df, keys in [
        ("observations", obs, ["station_id", "date"]),
        ("model_timeseries", model, ["cell_id", "date"]),
    ]:
        ndup = int(df.duplicated(keys).sum())
        _check_row(checks, f"duplicates:{name}", "BLOCKER", "PASS" if ndup == 0 else "FAIL", f"Duplicate key check for {name}", f"duplicates={ndup}")
    for name, df, key in [("stations", stations, "station_id"), ("cells", cells, "cell_id")]:
        ndup = int(df[key].duplicated().sum())
        _check_row(checks, f"ids:{name}", "BLOCKER", "PASS" if ndup == 0 else "FAIL", f"Unique IDs in {name}", f"duplicates={ndup}")

    try:
        _, mapping_summary = build_observation_operator(
            stations, cells, OperatorConfig(
                method="nearest",
                max_distance_m=cfg.max_mapping_distance_m,
                max_ground_level_delta_m=cfg.max_ground_level_delta_m,
            )
        )
        mapping_summary.to_csv(outdir / "admission_mapping_summary.csv", index=False)
        n_map_fail = int((mapping_summary["mapping_qc"] != "PASS").sum())
        _check_row(checks, "observation_support", "BLOCKER", "PASS" if n_map_fail == 0 else "FAIL",
                   "Stations have admissible support in the model grid", f"mapping_failures={n_map_fail}")
    except Exception as exc:
        mapping_summary = pd.DataFrame()
        _check_row(checks, "observation_support", "BLOCKER", "FAIL", "Observation-support mapping failed", str(exc))

    model_cell_ids = set(model["cell_id"].astype(str))
    missing_model_cells = sorted(set(cells["cell_id"].astype(str)) - model_cell_ids)
    _check_row(checks, "model_cell_coverage", "BLOCKER", "PASS" if not missing_model_cells else "FAIL",
               "Configured model cells have transient heads", f"missing_cells={missing_model_cells[:20]}")

    for col in ["used_in_wdm", "used_in_lhm_calibration"]:
        vals = stations[col].astype(str).str.lower().str.strip()
        bad = ~vals.isin(LINEAGE_VALUES)
        if bad.any():
            _check_row(checks, f"lineage:{col}", "BLOCKER", "FAIL", f"Invalid lineage values in {col}", ", ".join(sorted(vals[bad].unique())))
        else:
            _check_row(checks, f"lineage:{col}", "BLOCKER", "PASS", f"Lineage values explicit in {col}")
    hg = stations["heldout_group"].astype(str).str.lower().str.strip()
    bad_hg = ~hg.isin(HELDOUT_VALUES)
    _check_row(checks, "heldout_group_values", "BLOCKER", "PASS" if not bad_hg.any() else "FAIL", "Held-out group labels are valid", ", ".join(sorted(hg[bad_hg].unique())))
    n_heldout = int((hg == "heldout").sum())
    _check_row(checks, "heldout_available", "BLOCKER", "PASS" if n_heldout >= cfg.min_heldout_stations else "FAIL", "Held-out stations are reserved", f"n_heldout={n_heldout}")
    unknown_lineage = int(((stations["used_in_wdm"].astype(str).str.lower() == "unknown") | (stations["used_in_lhm_calibration"].astype(str).str.lower() == "unknown")).sum())
    _check_row(checks, "lineage_unknown", "WARNING", "WARN" if unknown_lineage else "PASS", "Unknown lineage is visible", f"stations_with_unknown={unknown_lineage}")

    station_rows: list[dict] = []
    for st in stations.itertuples(index=False):
        sid = str(st.station_id)
        o = obs[obs["station_id"].astype(str) == sid].sort_values("date")
        if o.empty:
            station_rows.append({"station_id": sid, "admission_status": "BLOCKED", "reason": "no observations"})
            continue
        start = o["date"].min(); end = o["date"].max()
        span_days = int((end - start).days + 1)
        forcing_in_span = forcing[(forcing["date"] >= start) & (forcing["date"] <= end)]
        expected = pd.date_range(start, end, freq="D")
        forcing_coverage = len(set(forcing_in_span["date"]) & set(expected)) / max(1, len(expected))
        daily_run = _daily_complete_run(o["date"])
        response_eligible = daily_run >= cfg.min_daily_complete_days_for_response and forcing_coverage >= cfg.forcing_coverage_min
        status = "PASS"
        reason = ""
        if span_days < cfg.min_overlap_days:
            status = "BLOCKED"; reason = f"observation span {span_days} d < minimum {cfg.min_overlap_days} d"
        station_rows.append({
            "station_id": sid,
            "obs_start": str(start.date()),
            "obs_end": str(end.date()),
            "obs_span_days": span_days,
            "n_observations": int(len(o)),
            "longest_daily_complete_run_days": daily_run,
            "forcing_coverage": float(forcing_coverage),
            "response_model_eligible": bool(response_eligible),
            "admission_status": status,
            "reason": reason,
            "used_in_wdm": getattr(st, "used_in_wdm"),
            "used_in_lhm_calibration": getattr(st, "used_in_lhm_calibration"),
            "heldout_group": getattr(st, "heldout_group"),
        })
    station_df = pd.DataFrame(station_rows)
    station_df.to_csv(outdir / "station_admission.csv", index=False)
    n_blocked_stations = int((station_df["admission_status"] == "BLOCKED").sum()) if not station_df.empty else len(stations)
    _check_row(checks, "station_overlap", "BLOCKER", "PASS" if n_blocked_stations == 0 else "FAIL", "Every configured station meets minimum observation span", f"blocked_stations={n_blocked_stations}")
    n_response = int(station_df.get("response_model_eligible", pd.Series(dtype=bool)).fillna(False).sum())
    _check_row(checks, "daily_response_eligibility", "WARNING", "PASS" if n_response else "WARN", "At least one station has a complete daily run for paired response fitting", f"eligible={n_response}/{len(station_df)}")
    short_recommended = int((station_df.get("obs_span_days", pd.Series(dtype=float)) < cfg.recommended_overlap_days).sum()) if not station_df.empty else 0
    _check_row(checks, "recommended_record_length", "WARNING", "WARN" if short_recommended else "PASS", "Recommended multi-year record length", f"stations_below_{cfg.recommended_overlap_days}d={short_recommended}")

    model_start, model_end = model["date"].min(), model["date"].max()
    force_start, force_end = forcing["date"].min(), forcing["date"].max()
    temporal_ok = pd.notna(model_start) and pd.notna(force_start) and force_start <= model_start and force_end >= model_end
    _check_row(checks, "forcing_model_period", "BLOCKER", "PASS" if temporal_ok else "FAIL", "Forcing covers model output period", f"model={model_start}..{model_end}; forcing={force_start}..{force_end}")

    flux_meta = _flux_metadata(model, flux_metadata_path, checks)
    run_meta = _run_metadata(run_metadata_path, checks)

    checks_df = pd.DataFrame(checks)
    checks_df.to_csv(outdir / "admission_checks.csv", index=False)
    blocker_fail = int(((checks_df["severity"] == "BLOCKER") & (checks_df["status"] == "FAIL")).sum())
    warnings = int((checks_df["status"] == "WARN").sum())
    verdict = "PASS" if blocker_fail == 0 else "BLOCKED"
    report = {
        "verdict": verdict,
        "blocker_failures": blocker_fail,
        "warnings": warnings,
        "n_stations": int(len(stations)),
        "n_heldout": n_heldout,
        "n_response_model_eligible": n_response,
        "n_mapping_pass": int((mapping_summary["mapping_qc"] == "PASS").sum()) if not mapping_summary.empty else 0,
        "config": cfg.as_dict(),
        "model_run_id": run_meta.get("model_run_id"),
        "model_version": run_meta.get("model_version"),
        "documented_process_variables": sorted(flux_meta["variable"].astype(str).tolist()) if not flux_meta.empty and "variable" in flux_meta else [],
    }
    (outdir / "admission_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>TS05 admission</title>
<style>body{{font-family:Arial,sans-serif;max-width:1300px;margin:36px auto;line-height:1.45}}table{{border-collapse:collapse;font-size:13px}}th,td{{border:1px solid #ccc;padding:5px 7px}}th{{background:#f2f2f2}}</style></head><body>
<h1>WDM-LHM TS05 real-data admission</h1>
<h2>Verdict: {verdict}</h2>
<p>The gate checks schema, lineage, held-out design, temporal coverage, model-grid support, process-flux semantics and model-run identity before diagnostic analysis is admitted.</p>
<h2>Summary</h2>{pd.DataFrame([report]).to_html(index=False)}
<h2>Checks</h2>{checks_df.to_html(index=False)}
<h2>Station eligibility</h2>{station_df.to_html(index=False)}
<h2>Observation support</h2>{mapping_summary.to_html(index=False, float_format=lambda x: f"{x:.3f}") if not mapping_summary.empty else '<p>No mapping summary available.</p>'}
</body></html>"""
    (outdir / "admission_report.html").write_text(html, encoding="utf-8")
    return {"verdict": verdict, "checks": checks_df, "stations": station_df, "mapping": mapping_summary, "report": report, "html": str(outdir / "admission_report.html")}
