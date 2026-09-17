# BRO GLD row-assessment status — design checkpoint

Status: **DESIGN_BOUNDARY_ESTABLISHED**

Date: 2026-09-17

## Capability

`BRO_GLD_ROW_ASSESSMENT_QUALITY_CONTRACT`

Phase: `DESIGN`

## Canonical source

- canonical `main` at workunit start: `d36a66213432ccc45b4f42898eb963812d3965e0`;
- branch: `work/bro-gld-assessment-status`.

## Triggering defect

The BRO GLD compact endpoint selected as `series_class=fully_assessed` contains a row-level assessment field. In the current live headerless format it is the third positional field and contains values including:

- `goedgekeurd`;
- `afgekeurd`;
- `onbeslist`.

The current `parse_gld_compact_csv()` retains only timestamp and head value. The row-level assessment status is dropped. `ingest_bro_groundwater()` then labels every parsed row from that endpoint `fully_assessed`, and downstream freatic screening computes empirical quantiles over all retained rows.

This incorrectly conflates the assessment class of the selected BRO series resource with the assessment outcome of each observation.

## Immutable evidence

Qualified TS07 source bundle:

- workflow run: `35109465960`;
- artifact: `10452120627` (`freatic-smoke-35109465960`);
- artifact digest: `b4770757f27d5bbd0e7e290bcfa187c3affb6f444293e0c83b22c7c4b90098f0`.

For `GMW000000020760_T1` / `GLD000000007463` the raw compact payload provenance is:

- endpoint: `objectsAsCsv/GLD000000007463?rapportagetype=compact&observatietype=regulier_beoordeeld`;
- raw payload SHA-256: `196a032698dd2f5f7e108c992c1321ad6521cafcb617de3b374b5b8cfe0797de`;
- raw payload size: 7,141,096 bytes.

The raw series includes a continuous block from 2018-12-15 through 2019-03-21 with physically implausible heads above local ground level. Those rows are explicitly marked `afgekeurd` by BRO. They were nevertheless included in the current TS07 `observations.csv` because the parser discarded the row-level status.

## Bounded impact audit

The ten TS07 series were checked against their immutable raw compact payloads.

Five older series contain no rejected rows in the inspected payloads and their current quantiles are unchanged:

- `GMW000000004037_T1`;
- `GMW000000004074_T1`;
- `GMW000000004074_T2`;
- `GMW000000004104_T1`;
- `GMW000000004104_T2`.

Five newer high-frequency series contain rejected rows and require requalification of empirical summaries after the parser fix:

| station | current rows | approved | rejected | current q05/q50/q95 m-mv | approved-only q05/q50/q95 m-mv |
|---|---:|---:|---:|---|---|
| `GMW000000020760_T1` | 107031 | 103976 | 2947 | 1.050 / 1.930 / 2.450 | 1.162 / 1.940 / 2.452 |
| `GMW000000020764_T1` | 31711 | 31417 | 267 | 0.334 / 1.060 / 1.749 | 0.333 / 1.054 / 1.731 |
| `GMW000000020774_T1` | 31704 | 31162 | 487 | 1.498 / 1.812 / 2.054 | 1.497 / 1.809 / 2.043 |
| `GMW000000020778_T1` | 31407 | 31006 | 311 | 0.714 / 1.477 / 2.207 | 0.713 / 1.470 / 2.202 |
| `GMW000000020781_T1` | 30827 | 30533 | 231 | 1.125 / 1.719 / 2.316 | 1.125 / 1.713 / 2.312 |

For 20760 specifically the raw status counts are:

- `goedgekeurd`: 103,976;
- `afgekeurd`: 2,947;
- `onbeslist`: 108.

Using only positively approved rows removes the above-ground block. Its q95 changes only slightly, but q05 shifts materially. This demonstrates that the issue is a provenance/quality-contract defect even where a final candidate ordering happens not to change.

## Scientific/data contract

### Acquisition and parsing

The parser must preserve row-level BRO assessment information rather than discard it.

At minimum each observation record must carry:

- the exact/trimmed raw assessment token when supplied by BRO;
- a normalized assessment token suitable for deterministic filtering.

No observation row is removed solely during acquisition/parsing because its assessment is rejected, undecided or unknown. Raw and parsed provenance remain inspectable.

Missing assessment status remains missing/unknown. It must never be silently converted to `goedgekeurd`.

### Scientific evidence selection

For a `fully_assessed` series used as scientific freatic evidence:

- `goedgekeurd` rows are eligible for empirical summaries;
- `afgekeurd` rows are not eligible evidence;
- `onbeslist` rows are not eligible evidence;
- unknown/unavailable row status is not favourable evidence.

The scientific layer must report how many rows were available and how many were actually admitted to the evidence calculation.

This filtering belongs in the evidence-selection/screening layer, not in the HTTP acquisition layer.

### Same-location vertical-head evidence

The same quality rule must be applied before daily aggregation for vertical-head comparisons. Rejected or undecided rows must not enter same-GMW hydraulic evidence merely because they came from a `fully_assessed` endpoint.

### Non-fully-assessed series

No new semantics are introduced for preliminary or unknown series in this workunit. Existing candidate restrictions remain. This workunit does not promote preliminary/unknown rows to positive evidence.

## Required implementation properties

1. Parse and retain row-level assessment status for both recognized headered compact CSV and the qualified live headerless positional format.
2. Preserve rejected/undecided rows in the parsed observation bundle.
3. Add deterministic quality selection for freatic scientific summaries.
4. Apply the same quality selection before vertical-head daily aggregation.
5. Add regression tests containing `goedgekeurd`, `afgekeurd` and `onbeslist` rows.
6. Report assessment-status counts or equivalent provenance in the ingest result/manifest.
7. Requalify TS07 empirical summaries from the immutable/live BRO source before resuming positive candidate adjudication.

## Existing evidence impact

The previously pinned 4074/4104 Stage-B adversarial cases are not numerically affected by rejected-row filtering in the inspected immutable payloads because all inspected rows are approved.

The five newer candidate/review series listed above are dependency-affected and their empirical summaries must be treated as superseded once the corrected pipeline is admitted.

The final 20774 disposition remains fail-closed under either quantile set; nevertheless its historical numeric TS07 summaries must not be treated as the corrected canonical figures after this workunit.

## Exclusions

This workunit does not:

- change BRO raw source data;
- invent a quality score;
- repair or interpolate rejected observations;
- reinterpret `afgekeurd` as a physical observation;
- infer freatic hydraulic continuity;
- enable `ADMISSIBLE_FREATIC`;
- alter REGIS/GeoTOP semantics;
- recalibrate LHM;
- expand Stage-B to the full GMW population.

## Verdict and next permitted action

`DESIGN_BOUNDARY_ESTABLISHED`

Next permitted action: implement the minimal parser + scientific evidence-selection correction, add regression tests, run ordinary CI, then perform a bounded TS07 requalification before any further positive-candidate adjudication.