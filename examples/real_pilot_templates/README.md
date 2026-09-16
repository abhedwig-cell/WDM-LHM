# Real pilot templates

These CSV files define the minimum practical bundle for TS05 admission and TS01–TS04 diagnostics.

Replace every example row with traceable real data. Do not infer missing provenance. `unknown` remains `unknown` until verified.

Required files:

- `stations.csv`: monitoring support, ground level, filter metadata and lineage.
- `cells.csv`: LHM/MODFLOW spatial support and run identity.
- `observations.csv`: measured groundwater heads.
- `model_timeseries.csv`: simulated heads and optional process fluxes.
- `forcing.csv`: precipitation/ET forcing used for paired response diagnostics.
- `flux_metadata.csv`: unit, sign and physical meaning of each process variable.
- `run_metadata.csv`: canonical model run/version/period identity.

Run `wdm-lhm admit ...` before interpreting any real-data diagnostic result.
