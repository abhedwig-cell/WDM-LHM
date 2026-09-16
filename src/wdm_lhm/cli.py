from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd
from .pipeline import run_station
from .synthetic import make_synthetic
from .synthetic_multi import make_multiwell_demo
from .batch import run_batch
from .observation_operator import OperatorConfig
from .regime_analysis import RegimeConfig
from .process_diagnosis import ProcessConfig
from .admission import AdmissionConfig, admit_bundle
from .bro_ingest import BROIngestConfig, ingest_bro_groundwater
from .freatic_screening import FreaticScreeningConfig, freatic_prescreen, vertical_head_pair_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="WDM-LHM paired groundwater diagnostics")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run diagnostics on one station file")
    p_run.add_argument("input")
    p_run.add_argument("output")
    p_run.add_argument("--station-id", default="station")

    p_demo = sub.add_parser("demo", help="Create and run a single-station synthetic demonstration")
    p_demo.add_argument("output")

    p_batch = sub.add_parser("batch", help="Run a multiwell batch with an explicit observation operator")
    p_batch.add_argument("observations")
    p_batch.add_argument("model_timeseries")
    p_batch.add_argument("stations")
    p_batch.add_argument("cells")
    p_batch.add_argument("forcing")
    p_batch.add_argument("output")
    p_batch.add_argument("--operator", choices=["nearest", "idw"], default="nearest")
    p_batch.add_argument("--k", type=int, default=4)
    p_batch.add_argument("--power", type=float, default=2.0)
    p_batch.add_argument("--max-distance-m", type=float, default=500.0)
    p_batch.add_argument("--max-ground-level-delta-m", type=float, default=1.0)
    p_batch.add_argument("--include-mapping-failures", action="store_true")
    p_batch.add_argument("--near-surface-cm", type=float, default=30.0)
    p_batch.add_argument("--min-regime-n", type=int, default=60)
    p_batch.add_argument("--block-days", type=int, default=30)
    p_batch.add_argument("--bootstrap-n", type=int, default=500)
    p_batch.add_argument("--cv-folds", type=int, default=5)
    p_batch.add_argument("--process-lags", default="0,1,3,7,14,30", help="Comma-separated calendar-day lags for TS04 screening")

    p_admit = sub.add_parser("admit", help="Validate a real-data pilot bundle before analysis")
    p_admit.add_argument("observations")
    p_admit.add_argument("model_timeseries")
    p_admit.add_argument("stations")
    p_admit.add_argument("cells")
    p_admit.add_argument("forcing")
    p_admit.add_argument("output")
    p_admit.add_argument("--flux-metadata", required=True)
    p_admit.add_argument("--run-metadata", required=True)
    p_admit.add_argument("--min-overlap-days", type=int, default=365)
    p_admit.add_argument("--recommended-overlap-days", type=int, default=1460)
    p_admit.add_argument("--min-daily-response-days", type=int, default=180)

    p_bro = sub.add_parser("bro-ingest", help="Build a real observation bundle from public BRO/PDOK services")
    p_bro.add_argument("output")
    p_bro.add_argument("--bbox", required=True, help="CRS84 bbox minlon,minlat,maxlon,maxlat")
    p_bro.add_argument("--min-observations", type=int, default=30)
    p_bro.add_argument("--min-span-days", type=int, default=365)
    p_bro.add_argument("--max-series", type=int)
    p_bro.add_argument("--no-preliminary", action="store_true")
    p_bro.add_argument("--include-unknown-series", action="store_true")
    p_bro.add_argument("--only-tubes-in-use", action="store_true")
    p_bro.add_argument("--force", action="store_true", help="Ignore cached source bytes")

    p_freatic = sub.add_parser("freatic-prescreen", help="Create conservative BRO-only freatic candidate evidence")
    p_freatic.add_argument("stations")
    p_freatic.add_argument("observations")
    p_freatic.add_argument("output")
    p_freatic.add_argument("--min-observations", type=int, default=100)
    p_freatic.add_argument("--min-span-days", type=int, default=730)
    p_freatic.add_argument("--legacy-max-screen-bottom-depth-m", type=float, default=5.0)
    p_freatic.add_argument("--allow-non-fully-assessed-candidate", action="store_true")
    p_freatic.add_argument("--vertical-min-overlap-days", type=int, default=30)

    p_demo_multi = sub.add_parser("demo-multi", help="Create and run a synthetic multiwell demonstration")
    p_demo_multi.add_argument("output")
    p_demo_multi.add_argument("--operator", choices=["nearest", "idw"], default="idw")
    p_demo_multi.add_argument("--near-surface-cm", type=float, default=30.0)
    p_demo_multi.add_argument("--min-regime-n", type=int, default=60)
    p_demo_multi.add_argument("--process-lags", default="0,1,3,7,14,30")

    args = parser.parse_args()
    if args.command == "run":
        result = run_station(args.input, args.output, args.station_id)
        print(result["report"])
    elif args.command == "demo":
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        csv = out / "synthetic_input.csv"
        make_synthetic().to_csv(csv, index=False)
        result = run_station(csv, out, "synthetic_demo")
        print(result["report"])
    elif args.command == "batch":
        cfg = OperatorConfig(
            method=args.operator,
            k=args.k,
            power=args.power,
            max_distance_m=args.max_distance_m,
            max_ground_level_delta_m=args.max_ground_level_delta_m,
        )
        rcfg = RegimeConfig(
            near_surface_cm=args.near_surface_cm,
            min_regime_n=args.min_regime_n,
            block_days=args.block_days,
            bootstrap_n=args.bootstrap_n,
            cv_folds=args.cv_folds,
        )
        pcfg = ProcessConfig(lags_days=tuple(int(x) for x in args.process_lags.split(",") if x.strip()))
        result = run_batch(args.observations, args.model_timeseries, args.stations, args.cells, args.forcing,
                           args.output, cfg, args.include_mapping_failures, rcfg, pcfg)
        print(result["report"])
    elif args.command == "bro-ingest":
        bbox = tuple(float(x) for x in args.bbox.split(","))
        if len(bbox) != 4:
            raise SystemExit("--bbox must contain minlon,minlat,maxlon,maxlat")
        cfg = BROIngestConfig(
            bbox_crs84=bbox, min_observations=args.min_observations, min_span_days=args.min_span_days,
            allow_preliminary=not args.no_preliminary, include_unknown_series=args.include_unknown_series,
            only_tubes_in_use=args.only_tubes_in_use, max_series=args.max_series,
        )
        result = ingest_bro_groundwater(args.output, cfg, force=args.force)
        print(json.dumps(result["manifest"], indent=2))
    elif args.command == "admit":
        acfg = AdmissionConfig(
            min_overlap_days=args.min_overlap_days,
            recommended_overlap_days=args.recommended_overlap_days,
            min_daily_complete_days_for_response=args.min_daily_response_days,
        )
        result = admit_bundle(
            args.observations, args.model_timeseries, args.stations, args.cells, args.forcing, args.output,
            flux_metadata_path=args.flux_metadata, run_metadata_path=args.run_metadata, config=acfg,
        )
        print(result["verdict"])
    elif args.command == "freatic-prescreen":
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        stations = pd.read_csv(args.stations)
        observations = pd.read_csv(args.observations)
        fcfg = FreaticScreeningConfig(
            min_observations=args.min_observations,
            min_span_days=args.min_span_days,
            legacy_max_screen_bottom_depth_m=args.legacy_max_screen_bottom_depth_m,
            require_fully_assessed_for_candidate=not args.allow_non_fully_assessed_candidate,
        )
        screen = freatic_prescreen(stations, observations, fcfg)
        vertical = vertical_head_pair_evidence(
            stations, observations, min_overlap_days=args.vertical_min_overlap_days
        )
        screen.to_csv(out / "freatic_prescreen.csv", index=False)
        vertical.to_csv(out / "vertical_head_pairs.csv", index=False)
        summary = {
            "config": fcfg.as_dict(),
            "counts": screen["prescreen_verdict"].value_counts(dropna=False).to_dict(),
            "vertical_pairs": int(len(vertical)),
        }
        (out / "freatic_prescreen_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
    else:
        out = Path(args.output)
        inp = out / "inputs"
        result_dir = out / "results"
        paths = make_multiwell_demo(inp)
        cfg = OperatorConfig(method=args.operator, k=4, power=2.0, max_distance_m=400.0, max_ground_level_delta_m=0.5)
        rcfg = RegimeConfig(near_surface_cm=args.near_surface_cm, min_regime_n=args.min_regime_n)
        pcfg = ProcessConfig(lags_days=tuple(int(x) for x in args.process_lags.split(",") if x.strip()))
        result = run_batch(paths["observations"], paths["model_timeseries"], paths["stations"], paths["cells"],
                           paths["forcing"], result_dir, cfg, regime_config=rcfg, process_config=pcfg)
        print(result["report"])


if __name__ == "__main__":
    main()
