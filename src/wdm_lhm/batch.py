from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .observation_operator import OperatorConfig, build_observation_operator, apply_observation_operator
from .pipeline import run_station
from .regime_analysis import RegimeConfig
from .process_diagnosis import ProcessConfig


def _read_table(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p)


def _forcing_for_station(forcing: pd.DataFrame, station_id: str) -> pd.DataFrame:
    f = forcing.copy()
    f["date"] = pd.to_datetime(f["date"], errors="raise")
    if "station_id" in f.columns:
        f = f[f["station_id"].astype(str) == str(station_id)].copy()
    return f[["date", "precip_mm", "et_mm"]]


def run_batch(
    observations_path: str | Path,
    model_timeseries_path: str | Path,
    stations_path: str | Path,
    cells_path: str | Path,
    forcing_path: str | Path,
    output_dir: str | Path,
    operator_config: OperatorConfig | None = None,
    include_mapping_failures: bool = False,
    regime_config: RegimeConfig | None = None,
    process_config: ProcessConfig | None = None,
) -> dict:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    station_out = outdir / "stations"
    station_out.mkdir(exist_ok=True)

    obs = _read_table(observations_path)
    mts = _read_table(model_timeseries_path)
    stations = _read_table(stations_path)
    cells = _read_table(cells_path)
    forcing = _read_table(forcing_path)

    obs_required = {"date", "station_id", "obs_head_mnap"}
    missing = obs_required - set(obs.columns)
    if missing:
        raise ValueError(f"observations missing required columns: {sorted(missing)}")
    force_required = {"date", "precip_mm", "et_mm"}
    missing = force_required - set(forcing.columns)
    if missing:
        raise ValueError(f"forcing missing required columns: {sorted(missing)}")

    obs["date"] = pd.to_datetime(obs["date"], errors="raise")
    operator, mapping_summary = build_observation_operator(stations, cells, operator_config)
    extracted = apply_observation_operator(mts, operator)
    operator.to_csv(outdir / "observation_operator.csv", index=False)
    mapping_summary.to_csv(outdir / "mapping_summary.csv", index=False)

    summary_rows: list[dict] = []
    failures: list[dict] = []
    process_rows: list[dict] = []

    for st in stations.itertuples(index=False):
        sid = str(st.station_id)
        map_row = mapping_summary[mapping_summary["station_id"].astype(str) == sid].iloc[0].to_dict()
        if map_row["mapping_qc"] != "PASS" and not include_mapping_failures:
            failures.append({"station_id": sid, "stage": "mapping", "reason": "mapping_qc=FAIL"})
            summary_rows.append({"station_id": sid, **map_row, "analysis_status": "SKIPPED_MAPPING_QC"})
            continue

        o = obs[obs["station_id"].astype(str) == sid][["date", "obs_head_mnap"]].copy()
        m = extracted[extracted["station_id"].astype(str) == sid].drop(columns=["station_id"]).copy()
        f = _forcing_for_station(forcing, sid)
        if o.empty:
            failures.append({"station_id": sid, "stage": "input", "reason": "no observations"})
            summary_rows.append({"station_id": sid, **map_row, "analysis_status": "NO_OBSERVATIONS"})
            continue
        if f.empty:
            failures.append({"station_id": sid, "stage": "input", "reason": "no forcing"})
            summary_rows.append({"station_id": sid, **map_row, "analysis_status": "NO_FORCING"})
            continue

        frame = m.merge(f, on="date", how="inner").merge(o, on="date", how="left")
        frame["ground_level_mnap"] = float(st.ground_level_mnap)
        if hasattr(st, "drain_level_mnap") and pd.notna(getattr(st, "drain_level_mnap")):
            frame["drain_level_mnap"] = float(getattr(st, "drain_level_mnap"))
        input_path = station_out / sid / "station_input.csv"
        input_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(input_path, index=False)

        try:
            result = run_station(input_path, input_path.parent, sid, regime_config=regime_config, process_config=process_config)
            response = {r["series"]: r for r in result["response"]}
            gxg = {r["series"]: r for r in result["gxg"]}
            for prow in result.get("ts04", {}).get("best_by_variable", []):
                process_rows.append({"station_id": sid, **prow})
            summary_rows.append({
                "station_id": sid,
                **map_row,
                "analysis_status": result.get("analysis_status", "PASS"),
                **{f"metric_{k}": v for k, v in result["metrics"].items()},
                "obs_ghg_cm": gxg["observed"]["ghg_cm"],
                "obs_gvg_cm": gxg["observed"]["gvg_cm"],
                "obs_glg_cm": gxg["observed"]["glg_cm"],
                "model_ghg_cm": gxg["model"]["ghg_cm"],
                "model_gvg_cm": gxg["model"]["gvg_cm"],
                "model_glg_cm": gxg["model"]["glg_cm"],
                "delta_ghg_cm": gxg["model"]["ghg_cm"] - gxg["observed"]["ghg_cm"],
                "delta_gvg_cm": gxg["model"]["gvg_cm"] - gxg["observed"]["gvg_cm"],
                "delta_glg_cm": gxg["model"]["glg_cm"] - gxg["observed"]["glg_cm"],
                "obs_tau_days": response["observed"].get("tau_days"),
                "model_tau_days": response["model"].get("tau_days"),
                "delta_tau_days": response["model"].get("tau_days") - response["observed"].get("tau_days"),
                "obs_response_status": response["observed"].get("fit_status", "PASS"),
                "model_response_status": response["model"].get("fit_status", "PASS"),
                "drain_effect_cm": result.get("ts03", {}).get("drain_effect", {}).get("effect_a_minus_b_cm"),
                "drain_effect_ci_low_cm": result.get("ts03", {}).get("drain_effect", {}).get("ci_low_cm"),
                "drain_effect_ci_high_cm": result.get("ts03", {}).get("drain_effect", {}).get("ci_high_cm"),
                "drain_effect_status": result.get("ts03", {}).get("drain_effect", {}).get("status"),
                "drain_hinge_cv_improvement_pct": result.get("ts03", {}).get("drain_hinge", {}).get("relative_improvement_pct"),
                "drain_hinge_status": result.get("ts03", {}).get("drain_hinge", {}).get("status"),
                "best_process_variable": result.get("ts04", {}).get("overall_best_process", {}).get("variable"),
                "best_process_lag_days": result.get("ts04", {}).get("overall_best_process", {}).get("lag_days"),
                "best_process_cv_improvement_pct": result.get("ts04", {}).get("overall_best_process", {}).get("relative_improvement_pct"),
                "best_process_evidence": result.get("ts04", {}).get("overall_best_process", {}).get("evidence_label"),
                "report": result["report"],
            })
        except Exception as exc:
            failures.append({"station_id": sid, "stage": "analysis", "reason": str(exc)})
            summary_rows.append({"station_id": sid, **map_row, "analysis_status": "FAILED", "error": str(exc)})

    summary = pd.DataFrame(summary_rows)
    failure_df = pd.DataFrame(failures)
    process_long = pd.DataFrame(process_rows)
    summary.to_csv(outdir / "station_summary.csv", index=False)
    failure_df.to_csv(outdir / "failures.csv", index=False)
    process_long.to_csv(outdir / "process_best_by_station_variable.csv", index=False)
    if not process_long.empty:
        q = process_long[process_long["status"] == "PASS"].copy()
        if not q.empty:
            process_area = q.groupby("variable", as_index=False).agg(
                n_stations_qualified=("station_id", "nunique"),
                median_cv_improvement_pct=("relative_improvement_pct", "median"),
                max_cv_improvement_pct=("relative_improvement_pct", "max"),
                median_selected_lag_days=("lag_days", "median"),
                n_follow_up=("evidence_label", lambda x: int(x.isin(["FOLLOW_UP", "STRONG_FOLLOW_UP"]).sum())),
                n_strong_follow_up=("evidence_label", lambda x: int((x == "STRONG_FOLLOW_UP").sum())),
            )
        else:
            process_area = pd.DataFrame()
    else:
        process_area = pd.DataFrame()
    process_area.to_csv(outdir / "process_area_summary.csv", index=False)

    manifest = {
        "n_stations": int(len(stations)),
        "n_mapping_pass": int((mapping_summary["mapping_qc"] == "PASS").sum()),
        "n_analysed": int((summary["analysis_status"].isin(["PASS", "PARTIAL"])).sum()) if not summary.empty else 0,
        "n_failures": int(len(failure_df)),
        "operator": (operator_config or OperatorConfig()).as_dict(),
        "regime": (regime_config or RegimeConfig()).as_dict(),
        "process": (process_config or ProcessConfig()).as_dict(),
    }
    (outdir / "batch_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    plot_files = _make_batch_plots(outdir, summary)
    _write_batch_report(outdir, summary, mapping_summary, manifest, plot_files, process_area)
    return {"summary": summary, "failures": failure_df, "process_area": process_area, "manifest": manifest, "report": str(outdir / "batch_report.html")}


def _make_batch_plots(outdir: Path, summary: pd.DataFrame) -> list[str]:
    files: list[str] = []
    ok = summary[summary.get("analysis_status", pd.Series(index=summary.index, dtype=object)).isin(["PASS", "PARTIAL"])].copy()
    if ok.empty:
        return files

    if {"obs_tau_days", "model_tau_days"}.issubset(ok.columns):
        d = ok[["obs_tau_days", "model_tau_days"]].dropna()
        if not d.empty:
            fig, ax = plt.subplots(figsize=(5.5, 5.0))
            ax.scatter(d["obs_tau_days"], d["model_tau_days"])
            lo = float(min(d.min()))
            hi = float(max(d.max()))
            ax.plot([lo, hi], [lo, hi], linewidth=1)
            ax.set_xlabel("Observed response time [days]")
            ax.set_ylabel("Model response time [days]")
            ax.set_title("Paired response time")
            fig.tight_layout()
            path = outdir / "paired_tau.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path.name)

    if {"station_id", "metric_std_ratio"}.issubset(ok.columns):
        d = ok[["station_id", "metric_std_ratio"]].dropna()
        if not d.empty:
            fig, ax = plt.subplots(figsize=(max(6, len(d)*0.8), 4))
            ax.bar(d["station_id"].astype(str), d["metric_std_ratio"])
            ax.axhline(1.0, linewidth=1)
            ax.set_ylabel("Model / observed standard deviation")
            ax.set_xlabel("Station")
            ax.set_title("Transient amplitude ratio")
            fig.tight_layout()
            path = outdir / "std_ratio_by_station.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path.name)

    if {"station_id", "drain_effect_cm", "drain_effect_ci_low_cm", "drain_effect_ci_high_cm", "drain_effect_status"}.issubset(ok.columns):
        d = ok[ok["drain_effect_status"] == "PASS"][["station_id", "drain_effect_cm", "drain_effect_ci_low_cm", "drain_effect_ci_high_cm"]].dropna()
        if not d.empty:
            fig, ax = plt.subplots(figsize=(max(6, len(d)*0.9), 4))
            yerr = np.vstack([
                d["drain_effect_cm"].to_numpy(float) - d["drain_effect_ci_low_cm"].to_numpy(float),
                d["drain_effect_ci_high_cm"].to_numpy(float) - d["drain_effect_cm"].to_numpy(float),
            ])
            ax.errorbar(d["station_id"].astype(str), d["drain_effect_cm"], yerr=yerr, fmt="o", capsize=3)
            ax.axhline(0.0, linewidth=1)
            ax.set_ylabel("Residual effect [cm]")
            ax.set_xlabel("Station")
            ax.set_title("Drain-active minus inactive residual, block-bootstrap 95% CI")
            fig.tight_layout()
            path = outdir / "drain_effect_by_station.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path.name)

    if {"station_id", "drain_hinge_cv_improvement_pct", "drain_hinge_status"}.issubset(ok.columns):
        d = ok[ok["drain_hinge_status"] == "PASS"][["station_id", "drain_hinge_cv_improvement_pct"]].dropna()
        if not d.empty:
            fig, ax = plt.subplots(figsize=(max(6, len(d)*0.9), 4))
            ax.bar(d["station_id"].astype(str), d["drain_hinge_cv_improvement_pct"])
            ax.axhline(0.0, linewidth=1)
            ax.set_ylabel("Blocked-CV RMSE improvement [%]")
            ax.set_xlabel("Station")
            ax.set_title("Added predictive value of drain-level hinge")
            fig.tight_layout()
            path = outdir / "drain_hinge_cv_improvement.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path.name)

    if {"station_id", "best_process_cv_improvement_pct", "best_process_variable"}.issubset(ok.columns):
        d = ok[["station_id", "best_process_cv_improvement_pct", "best_process_variable"]].dropna()
        if not d.empty:
            fig, ax = plt.subplots(figsize=(max(6, len(d)*0.9), 4))
            ax.bar(d["station_id"].astype(str), d["best_process_cv_improvement_pct"])
            ax.axhline(0.0, linewidth=1)
            ax.set_ylabel("Blocked-CV RMSE improvement [%]")
            ax.set_xlabel("Station")
            ax.set_title("Best exploratory process signal per station")
            for i, (_, row) in enumerate(d.iterrows()):
                ax.text(i, float(row["best_process_cv_improvement_pct"]), str(row["best_process_variable"]), rotation=90, va="bottom", ha="center", fontsize=8)
            fig.tight_layout()
            path = outdir / "best_process_improvement.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path.name)
    return files


def _write_batch_report(outdir: Path, summary: pd.DataFrame, mapping_summary: pd.DataFrame, manifest: dict, plot_files: list[str], process_area: pd.DataFrame) -> None:
    cols = [c for c in [
        "station_id", "mapping_qc", "nearest_distance_m", "ground_level_delta_m", "analysis_status",
        "metric_bias", "metric_rmse", "metric_corr", "metric_std_ratio", "delta_ghg_cm", "delta_gvg_cm", "delta_glg_cm", "obs_tau_days", "model_tau_days", "delta_tau_days",
        "drain_effect_cm", "drain_effect_ci_low_cm", "drain_effect_ci_high_cm", "drain_effect_status",
        "drain_hinge_cv_improvement_pct", "drain_hinge_status", "best_process_variable", "best_process_lag_days",
        "best_process_cv_improvement_pct", "best_process_evidence", "obs_response_status", "model_response_status"
    ] if c in summary.columns]
    body = summary[cols].to_html(index=False, float_format=lambda x: f"{x:.3f}") if not summary.empty else "<p>No stations analysed.</p>"
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>WDM-LHM TS04 batch report</title>
<style>body{{font-family:Arial,sans-serif;max-width:1300px;margin:36px auto;line-height:1.45}}table{{border-collapse:collapse;font-size:13px}}th,td{{border:1px solid #ccc;padding:5px 7px}}th{{background:#f2f2f2}}</style></head><body>
<h1>WDM-LHM TS04 multiwell process qualification</h1>
<p>This batch combines the explicit observation operator, paired time-series diagnostics, regime analysis and exploratory process-flux screening. Process associations are predictive diagnostics, not causal attribution.</p>
<h2>Manifest</h2>{pd.DataFrame([manifest]).to_html(index=False)}
<h2>Station results</h2>{body}
<h2>Area process screen</h2>{process_area.to_html(index=False, float_format=lambda x: f"{x:.3f}") if not process_area.empty else "<p>No qualified area-level process screen.</p>"}
<h2>Area diagnostics</h2>{"".join(f"<img src={pf!r} style='max-width:650px;margin:12px;'>" for pf in plot_files)}
<h2>Mapping QC</h2>{mapping_summary.to_html(index=False, float_format=lambda x: f"{x:.3f}")}
</body></html>"""
    (outdir / "batch_report.html").write_text(html, encoding="utf-8")
