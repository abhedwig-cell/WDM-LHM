# Conceptual model for freatic screening

Status: design model for issue #2.

## 1. Entities

For each candidate monitoring tube `i`:

- `GMW_i`: monitoring-well identity and ground-level metadata;
- `Tube_i`: screen top/bottom, status and use metadata;
- `GLD_i(t)`: observed groundwater level / hydraulic-head series;
- `Peer_i`: optional shallower/deeper filters at the same GMW or immediately colocated well;
- `Hydro_i`: hydrogeological context, when available;
- `Support_i`: spatial relation to the LHM/MODFLOW observation operator;
- `Lineage_i`: use in WDM and LHM calibration.

## 2. Information flow

```text
BRO GMW / Tube metadata -----> structural evidence ----\
BRO GLD series --------------> dynamic evidence -------+--> evidence record --> screening verdict
same-well peer filters ------> vertical-head evidence -+
hydrogeological context -----> confinement evidence ---+
LHM support + lineage -------> use-context evidence ---/
```

The screening verdict is therefore a property of the **tube-for-purpose pair**, not an intrinsic permanent label on the BRO object.

## 3. Purpose-specific interpretation

A series can be valid for one purpose and inadmissible for another. For example, a deep piezometer may be highly valuable for regional groundwater-flow calibration while being unsuitable as a direct observation of shallow groundwater depth for WDM comparison.

The initial purpose implemented here is:

> use as an observation of local freatic groundwater depth for paired WDM/LHM diagnostics.

## 4. Evidence classes

### A. Structural evidence

Derived directly from metadata:

- known local ground level;
- known and ordered screen top/bottom elevations;
- screen depths below ground level;
- tube status and `tube_in_use`;
- availability of fully assessed GLD data.

### B. Dynamic evidence

Derived from the measured series:

- number of measurements and record span;
- temporal continuity and cadence;
- observed head/depth quantiles;
- fraction of observations above local ground level;
- robust amplitude and long-term drift diagnostics.

These describe the measured pressure response but do **not** alone prove freatic connection.

### C. Vertical-head evidence

Where multiple filters share a well location, contemporaneous measurements are paired. We record:

- overlap count and time span;
- median and robust spread of head difference;
- sign persistence;
- correlation and dynamic similarity.

Persistent differences across depth are evidence against treating all filters as one freatic state.

### D. Hydrogeological evidence

Examples include:

- known aquitard or stagnating layer between surface system and screen;
- confined/semi-confined unit classification;
- perched groundwater setting;
- documented open homogeneous profile.

This layer can overrule simplistic geometric depth indicators.

## 5. Decision semantics

### `ADMISSIBLE_FREATIC`

Requires sufficient metadata and time-series support, no demonstrated conflicting vertical/hydrogeological evidence, and positive evidence consistent with shallow unconfined observation. Automatic admission must be conservative.

### `REVIEW_REQUIRED`

Default for plausible but unproven cases, for example a deeper screen without hydrogeological context, conflicting indicators, or a potentially meaningful vertical gradient that has not yet been physically interpreted.

### `NOT_ADMISSIBLE_FREATIC`

Used only when available evidence positively contradicts the freatic observation contract, for example a screen in a documented confined unit with a persistent head difference from a qualified shallow filter.

### `INSUFFICIENT_DATA`

Used when mandatory construction or series information is missing. Missing information is not converted into a favourable assumption.

## 6. Risk indicators versus decision evidence

The following may be useful risk indicators but are not standalone rejection rules:

- screen bottom deeper than the historical 5 m Gd criterion;
- screen wholly below the empirical water-level range;
- low correlation with a shallower peer filter;
- above-ground hydraulic heads;
- inactive/unknown tube status.

Each indicator is stored explicitly in the evidence record so later changes to policy do not require recomputing raw evidence.

## 7. Separation from observation operator

Freatic suitability and spatial representativeness are separate gates. A tube can be genuinely freatic but still poorly represent a 250 m or larger MODFLOW cell because of local drainage, topography or surface-water proximity.

Therefore:

```text
freatic screening PASS != observation-operator PASS
```

Both are required before the tube is admitted to the final paired validation set.
