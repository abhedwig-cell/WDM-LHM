# Real pilot input contract

Before interpreting model residuals, replace all example rows with traceable real data and document:

- coordinate reference system for `x_rd`, `y_rd`;
- exact LHM/MODFLOW run ID, model version, period and layer represented by `model_head_mnap`;
- observation source and quality flags;
- local ground-level source and datum;
- filter top/bottom and whether the filter represents the freatic system;
- drainage/surface-water level provenance;
- whether each monitoring well was used by WDM;
- whether each monitoring well was used for LHM/MODFLOW calibration or validation;
- which wells or periods are reserved as held-out validation.

Do not mark `unknown` as `no`. Unknown provenance remains unknown until verified.

## TS04 additional requirement: flux semantics

For every optional model flux column used in TS04, document:

- physical process represented;
- unit;
- sign convention;
- spatial support / model package of origin;
- whether the flux is a direct MODFLOW budget term, MetaSWAP-derived term or post-processed quantity;
- temporal aggregation represented by each timestamp.

Without this metadata TS04 may screen the variable numerically, but physical interpretation remains `NOT_ADMITTED`.
