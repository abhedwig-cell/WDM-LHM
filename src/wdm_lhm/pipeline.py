from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from .gxg import calculate_gxg
from .io import read_timeseries
from .metrics import paired_metrics
from .regimes import residual_regime_table, direction_regime_table
from .response_model import fit_linear_reservoir
from .report import make_plots, write_html_report
from .regime_analysis import (
    RegimeConfig,
    prepare_state_frame,
    regime_tables,
    regime_effects,
    piecewise_diagnostic,
    flux_diagnostics,
)
from .process_diagnosis import ProcessConfig, screen_process_variables, select_exploratory_best, overall_best_process


def _safe_response(series_name: str, target: pd.Series, precip: pd.Series, et: pd.Series) -> dict:
    try:
        out = fit_linear_reservoir(target, precip, et).as_dict()
        return {"series": series_name, "fit_status": "PASS", "fit_message": "", **out}
    except Exception as exc:
        return {
            "series": series_name,
            "fit_status": "NOT_QUALIFIED",
            "fit_message": str(exc),
            "offset": np.nan,
            "gain": np.nan,
            "memory_a": np.nan,
            "tau_days": np.nan,
            "rmse": np.nan,
            "n": int(pd.concat([target, precip, et], axis=1).dropna().shape[0]),
        }


def run_station(
    input_path: str | Path,
    output_dir: str | Path,
    station_id: str = "station",
    regime_config: RegimeConfig | None = None,
    process_config: ProcessConfig | None = None,
) -> dict:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    config = regime_config or RegimeConfig()
    pconfig = process_config or ProcessConfig()
    df = read_timeseries(input_path)

    metrics = paired_metrics(df["obs_depth_cm"], df["model_depth_cm"])
    obs_gxg = calculate_gxg(df["obs_depth_cm"]).as_dict()
    mod_gxg = calculate_gxg(df["model_depth_cm"]).as_dict()
    gxg_df = pd.DataFrame([{"series": "observed", **obs_gxg}, {"series": "model", **mod_gxg}])

    response_df = pd.DataFrame([
        _safe_response("observed", df["obs_depth_cm"], df["precip_mm"], df["et_mm"]),
        _safe_response("model", df["model_depth_cm"], df["precip_mm"], df["et_mm"]),
    ])

    regimes = residual_regime_table(df["obs_depth_cm"], df["model_depth_cm"])
    directions = direction_regime_table(df["obs_depth_cm"], df["model_depth_cm"])

    state = prepare_state_frame(df, config)
    tables = regime_tables(state)
    effects = regime_effects(state, config)
    piecewise = piecewise_diagnostic(state, config)
    fluxes = flux_diagnostics(state)

    process_screen = screen_process_variables(state, config=pconfig)
    process_best = select_exploratory_best(process_screen)
    process_overall = overall_best_process(process_best)

    df.to_csv(outdir / "harmonized_timeseries.csv")
    state.to_csv(outdir / "state_diagnostics_timeseries.csv")
    gxg_df.to_csv(outdir / "gxg.csv", index=False)
    response_df.to_csv(outdir / "response_models.csv", index=False)
    regimes.to_csv(outdir / "residual_depth_regimes.csv", index=False)
    directions.to_csv(outdir / "residual_direction_regimes.csv", index=False)
    for name, table in tables.items():
        table.to_csv(outdir / f"ts03_regime_{name}.csv", index=False)
    effects.to_csv(outdir / "ts03_regime_effects.csv", index=False)
    piecewise.to_csv(outdir / "ts03_piecewise_cv.csv", index=False)
    fluxes.to_csv(outdir / "ts03_flux_diagnostics.csv", index=False)
    process_screen.to_csv(outdir / "ts04_process_lag_screen.csv", index=False)
    process_best.to_csv(outdir / "ts04_process_best_by_variable.csv", index=False)
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (outdir / "regime_config.json").write_text(json.dumps(config.as_dict(), indent=2), encoding="utf-8")
    (outdir / "process_config.json").write_text(json.dumps(pconfig.as_dict(), indent=2), encoding="utf-8")
    plots = make_plots(df, outdir)
    report = write_html_report(
        outdir, station_id, metrics, gxg_df, response_df, regimes, plots,
        ts03_tables=tables, ts03_effects=effects, ts03_piecewise=piecewise, ts03_fluxes=fluxes,
        ts04_screen=process_screen, ts04_best=process_best,
    )

    analysis_status = "PASS" if (response_df["fit_status"] == "PASS").all() else "PARTIAL"
    drain_effect = effects.loc[effects["effect"] == "drain_active_minus_inactive"] if not effects.empty else pd.DataFrame()
    drain_effect_row = drain_effect.iloc[0].to_dict() if not drain_effect.empty else {}
    hinge = piecewise.loc[piecewise["model"] == "drain_level_hinge"] if not piecewise.empty else pd.DataFrame()
    hinge_row = hinge.iloc[0].to_dict() if not hinge.empty else {}

    return {
        "station_id": station_id,
        "report": str(report),
        "analysis_status": analysis_status,
        "metrics": metrics,
        "gxg": gxg_df.to_dict(orient="records"),
        "response": response_df.to_dict(orient="records"),
        "ts04": {
            "overall_best_process": process_overall,
            "best_by_variable": process_best.to_dict(orient="records"),
            "process_config": pconfig.as_dict(),
        },
        "ts03": {
            "drain_effect": drain_effect_row,
            "drain_hinge": hinge_row,
            "regime_config": config.as_dict(),
        },
    }
