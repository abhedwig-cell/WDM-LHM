from __future__ import annotations

from pathlib import Path
import html
import matplotlib.pyplot as plt
import pandas as pd


def make_plots(df: pd.DataFrame, outdir: Path) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    files = []

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df["obs_depth_cm"], label="Observed")
    ax.plot(df.index, df["model_depth_cm"], label="LHM/MODFLOW")
    ax.invert_yaxis()
    ax.set_ylabel("Groundwater depth [cm below ground]")
    ax.set_xlabel("Date")
    ax.legend()
    fig.tight_layout()
    p = outdir / "timeseries.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    files.append(p.name)

    residual = df["model_depth_cm"] - df["obs_depth_cm"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.scatter(df["model_depth_cm"], residual, s=8, alpha=0.35)
    ax.axhline(0, linewidth=1)
    if "drain_level_mnap" in df.columns and "ground_level_mnap" in df.columns:
        drain_depth = ((df["ground_level_mnap"] - df["drain_level_mnap"]) * 100.0).dropna()
        if not drain_depth.empty:
            ax.axvline(float(drain_depth.median()), linewidth=1, linestyle="--", label="Drain level")
            ax.legend()
    ax.set_xlabel("Simulated groundwater depth [cm]")
    ax.set_ylabel("Model - observation residual [cm]")
    fig.tight_layout()
    p = outdir / "residual_vs_depth.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    files.append(p.name)
    return files


def _table_or_note(df: pd.DataFrame | None, note: str = "No qualified result.") -> str:
    if df is None or df.empty:
        return f"<p>{html.escape(note)}</p>"
    return df.to_html(index=False, float_format=lambda x: f"{x:.3f}")


def write_html_report(
    outdir: Path,
    station_id: str,
    metrics: dict,
    gxg: pd.DataFrame,
    response: pd.DataFrame,
    regimes: pd.DataFrame,
    plot_files: list[str],
    ts03_tables: dict[str, pd.DataFrame] | None = None,
    ts03_effects: pd.DataFrame | None = None,
    ts03_piecewise: pd.DataFrame | None = None,
    ts03_fluxes: pd.DataFrame | None = None,
    ts04_screen: pd.DataFrame | None = None,
    ts04_best: pd.DataFrame | None = None,
) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "report.html"
    imgs = "\n".join(f'<img src="{html.escape(p)}" style="max-width:100%; margin:12px 0;">' for p in plot_files)
    ts03_tables = ts03_tables or {}
    ts03_html = ""
    if ts03_tables or ts03_effects is not None or ts03_piecewise is not None:
        ts03_html = f"""
<h2>TS03 state-dependent residual diagnostics</h2>
<p><strong>Interpretation:</strong> these are diagnostic associations, not a calibrated correction model and not proof of causality. Confidence intervals for binary regime effects use moving-block bootstrap. Piecewise models are compared with blocked cross-validation.</p>
<h3>Drainage regime</h3>{_table_or_note(ts03_tables.get('drain'))}
<h3>Near-surface regime</h3>{_table_or_note(ts03_tables.get('surface'))}
<h3>Rising versus falling</h3>{_table_or_note(ts03_tables.get('direction'))}
<h3>Season</h3>{_table_or_note(ts03_tables.get('season'))}
<h3>Block-bootstrap regime effects</h3>{_table_or_note(ts03_effects)}
<h3>Blocked-CV piecewise diagnostic</h3>{_table_or_note(ts03_piecewise)}
<h3>Optional model-flux associations</h3>{_table_or_note(ts03_fluxes, 'No optional model fluxes supplied or qualified.')}
"""
    ts04_html = ""
    if ts04_screen is not None or ts04_best is not None:
        ts04_html = f"""
<h2>TS04 process diagnostics</h2>
<p><strong>Interpretation:</strong> each process variable is tested for incremental predictive value beyond simulated groundwater depth, daily change in simulated depth and annual seasonality. Lags are screened with blocked cross-validation. Best-lag selection is exploratory and must be confirmed on held-out stations or periods before any physical or causal claim.</p>
<h3>Exploratory best lag by process variable</h3>{_table_or_note(ts04_best, 'No qualified process variables.')}
<h3>All lag-screen results</h3>{_table_or_note(ts04_screen, 'No process screen available.')}
"""
    body = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>TS03 {html.escape(station_id)}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1200px;margin:40px auto;line-height:1.5}} table{{border-collapse:collapse;font-size:13px}} th,td{{border:1px solid #ccc;padding:6px 9px}} th{{background:#f3f3f3}} code{{background:#f4f4f4;padding:2px 4px}}</style></head>
<body>
<h1>WDM-LHM TS04 process diagnostic: {html.escape(station_id)}</h1>
<p>This report separates transient model diagnosis from statistical correction. It does not create a new physically consistent MODFLOW state.</p>
<h2>Paired metrics on groundwater depth</h2>{pd.DataFrame([metrics]).to_html(index=False, float_format=lambda x: f'{x:.3f}')}
<h2>GxG comparison</h2>{gxg.to_html(index=False, float_format=lambda x: f'{x:.2f}')}
<h2>Paired response-model parameters</h2>{response.to_html(index=False, float_format=lambda x: f'{x:.4f}')}
<h2>Residual by simulated depth quantile</h2>{regimes.to_html(index=False, float_format=lambda x: f'{x:.2f}')}
{ts03_html}
{ts04_html}
<h2>Plots</h2>{imgs}
</body></html>"""
    path.write_text(body, encoding="utf-8")
    return path
