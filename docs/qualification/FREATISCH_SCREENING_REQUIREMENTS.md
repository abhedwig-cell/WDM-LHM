# Freatic monitoring-tube screening requirements

Status: TS07 design and qualification contract.

The live BRO ingest demonstrates why technical availability filtering must be separated from hydrological suitability. Long, fully assessed GLD series can come from filters that are too deep or otherwise not representative of the freatic groundwater table required for WDM/LHM comparison.

## Required separation

TS07 uses two stages.

### Stage A — BRO-only pre-screen

Purpose: efficiently route available BRO tubes using reproducible metadata and time-series evidence, without claiming that a candidate is physically proven freatic.

Allowed verdicts:

- `CANDIDATE_FREATIC`
- `REVIEW_DEEP_OR_AMBIGUOUS`
- `INSUFFICIENT_DATA`
- `NOT_USABLE_SERIES`

Stage A must report at least:

- screen top and bottom depth below local ground level;
- record count and span;
- robust groundwater/head-depth quantiles;
- series assessment class;
- tube status and in-use metadata where available;
- the historical Gd 5 m screen-bottom indicator as `legacy_gd_depth_risk`;
- reason codes supporting the routing result.

The historical 5 m criterion may be used as a transparent routing rule because it is documented in the groundwater-dynamics methodology. It must not be described as a universal physical definition of freatic connection.

### Stage B — scientific freatic admission

Purpose: decide whether a tube may be used as a freatic observation for the stated WDM/LHM analysis.

Allowed verdicts:

- `ADMISSIBLE_FREATIC`
- `REVIEW_REQUIRED`
- `NOT_ADMISSIBLE_FREATIC`
- `INSUFFICIENT_DATA`

Stage B must consider additional evidence where relevant:

- whether the filter is in, immediately below, or hydraulically connected to the groundwater-table fluctuation zone;
- evidence for confined, semi-confined or perched conditions;
- same-location multi-filter head differences;
- groundwater-head plausibility relative to local ground level and hydrogeology;
- local spatial representativeness relative to the LHM observation operator;
- WDM and LHM calibration lineage.

Uncertain or missing evidence must resolve to `REVIEW_REQUIRED` or `INSUFFICIENT_DATA`, never silently to admission.

## Multi-filter evidence

For multiple filters at one GMW location, contemporaneous daily heads should be paired and the following reported without a hidden rejection threshold:

- overlap count and period;
- median shallow-minus-deep head difference;
- robust spread of the difference;
- sign persistence;
- daily correlation.

A numeric vertical-gradient rejection threshold is not canonical until measurement precision and hydrological significance have been explicitly justified.

## Required guardrails

- Do not introduce a hidden single screen-depth threshold as a proxy for physical freatic suitability.
- Do not infer `unconfined` merely because no confining information is available.
- Do not infer that `fully_assessed` GLD measurements imply freatic representativeness.
- Do not convert missing metadata to zero, false or favourable status.
- Keep freatic suitability separate from spatial observation-support suitability.
- Keep freatic suitability separate from held-out/lineage admission.

## Qualification evidence

TS07 is qualified only when:

1. theory, conceptual and formal documents are linked;
2. synthetic tests cover shallow-candidate, deep-review, missing-geometry, insufficient-series, multi-filter and fail-closed admission behaviour;
3. the full pre-existing CI suite remains green;
4. a live BRO/PDOK workflow produces machine-readable Stage-A evidence on real tubes;
5. live results are interpreted as a pre-screen, not as final freatic admission.

See:

- `FREATIC_SCREENING_THEORY.md`
- `FREATIC_SCREENING_CONCEPTUAL_MODEL.md`
- `FREATIC_SCREENING_FORMAL_MODEL.md`
