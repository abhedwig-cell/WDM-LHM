# BRO GLD row-assessment status — qualification checkpoint

Status: **QUALIFIED_BRO_GLD_ROW_ASSESSMENT_CONTRACT**

Date: 2026-09-17

## Capability

`BRO_GLD_ROW_ASSESSMENT_QUALITY_CONTRACT`

## Phase

`QUALIFY`

## Canonical and branch state

- canonical `main` dependency: `d36a66213432ccc45b4f42898eb963812d3965e0`;
- branch: `work/bro-gld-assessment-status`;
- implementation head qualified by live runs: `d2c8a9ba40531d1c5c0daa9d2787e658f827d905`;
- PR: `#16`.

## Triggering defect

The BRO `regulier_beoordeeld` / `fully_assessed` compact CSV contains a row-level assessment field. The pre-existing parser discarded that field and downstream freatic screening therefore treated rejected and undecided rows as fully assessed scientific evidence.

The corrected contract separates acquisition provenance from scientific evidence selection:

- all parsed rows remain in the observation bundle;
- raw and normalized row-level assessment status are retained;
- `goedgekeurd` is the only admitted row-level status for `fully_assessed` scientific freatic evidence;
- `afgekeurd`, `onbeslist`, missing and unrecognized statuses remain inspectable but are not promoted to scientific evidence;
- the same rule is applied before same-location daily vertical-head aggregation.

No quality score or repaired/interpolated observation is introduced.

## Reused evidence

Original qualified TS07 artifact:

- workflow run: `35109465960`;
- artifact: `10452120627`;
- digest: `b4770757f27d5bbd0e7e290bcfa187c3affb6f444293e0c83b22c7c4b90098f0`.

Design checkpoint:

- `docs/qualification/BRO_GLD_ASSESSMENT_STATUS_DESIGN.md`.

## Qualification runs on implementation head

### Ordinary CI

Run `35216362739`: **PASS**.

- Python 3.10: PASS;
- Python 3.12: PASS;
- Python 3.12 test count: **168 passed**.

The preceding CI run correctly exposed one stale synthetic fixture that omitted row-level status while claiming fully assessed scientific evidence. That fixture was corrected by marking its synthetic observations explicitly `goedgekeurd`; no production rule was weakened.

### BRO live smoke

Run `35216362790`: **PASS**.

### Freatic prescreen live smoke

Run `35216362746`: **PASS**.

Artifact:

- ID: `10495082246`;
- name: `freatic-smoke-35216362746`;
- digest: `eeb19fd1684b344686d2ac72bc14f95e8c01c7fe248162b9ad9e3d43b64cdab8`.

Live ingest counts:

- GMW: 280;
- monitoring tubes: 374;
- GLD objects: 530;
- selected series: 10;
- stations: 10;
- parsed observations retained in provenance: 254,360;
- failures: 0.

Live row-level assessment counts:

- `goedgekeurd`: 249,774;
- `afgekeurd`: 4,243;
- `onbeslist`: 343.

## Requalified TS07 scientific summaries

The screening layer now reports only admitted `goedgekeurd` rows as `n_observations` for fully assessed scientific evidence.

| station | admitted n | q05 m-mv | q50 m-mv | q95 m-mv | above-ground fraction | screen top minus q95 m | Stage-A result |
|---|---:|---:|---:|---:|---:|---:|---|
| `GMW000000004037_T1` | 507 | 0.590 | 1.120 | 1.510 | 0.000 | -0.880 | `CANDIDATE_FREATIC` |
| `GMW000000004074_T1` | 433 | 2.246 | 2.580 | 2.794 | 0.000 | -0.584 | `REVIEW_DEEP_OR_AMBIGUOUS` |
| `GMW000000004074_T2` | 420 | 2.360 | 2.830 | 3.160 | 0.000 | 7.930 | `REVIEW_DEEP_OR_AMBIGUOUS` |
| `GMW000000004104_T1` | 19,547 | 2.739 | 3.224 | 3.620 | 0.000 | 8.400 | `REVIEW_DEEP_OR_AMBIGUOUS` |
| `GMW000000004104_T2` | 773 | 3.056 | 3.460 | 3.814 | 0.000 | 32.166 | `REVIEW_DEEP_OR_AMBIGUOUS` |
| `GMW000000020760_T1` | 103,976 | 1.162 | 1.940 | 2.452 | 0.000 | 0.485 | `CANDIDATE_FREATIC` |
| `GMW000000020764_T1` | 31,417 | 0.333 | 1.054 | 1.731 | 0.000 | 2.009 | `CANDIDATE_FREATIC` |
| `GMW000000020774_T1` | 31,162 | 1.497 | 1.809 | 2.043 | 0.000 | 1.287 | `CANDIDATE_FREATIC` |
| `GMW000000020778_T1` | 31,006 | 0.713 | 1.470 | 2.202 | 0.000 | 5.668 | `REVIEW_DEEP_OR_AMBIGUOUS` |
| `GMW000000020781_T1` | 30,533 | 1.125 | 1.713 | 2.312 | 0.000 | 1.268 | `CANDIDATE_FREATIC` |

The five newer high-frequency series therefore supersede their earlier empirical TS07 summaries. Their routing verdicts do not change under the corrected evidence contract.

For `GMW000000020760_T1`, the previously apparent above-ground block disappears from admitted scientific evidence because it was explicitly rejected by BRO. Its corrected direct summary is `1.162 / 1.940 / 2.452 m-mv` for q05/q50/q95.

## Same-location vertical-head evidence

The corrected live artifact preserves the previously qualified 4074/4104 pair evidence:

### GMW000000004074

- overlap days: 418;
- median shallow minus deep head: `+0.27 m`;
- robust sigma: `0.133434 m`;
- positive sign fraction: `0.980861`;
- daily correlation: `0.792298`.

### GMW000000004104

- overlap days: 772;
- median shallow minus deep head: `+0.12 m`;
- robust sigma: `0.103782 m`;
- positive sign fraction: `0.936528`;
- daily correlation: `0.922294`.

Thus the existing Stage-B adversarial interpretation for 4074/4104 is not numerically altered by this correction.

## Reproducible file hashes from live artifact

- `bro/bundle/observations.csv`: `59b69315a9d6841a3d639e56550d546810f9b6451d282e4894864e424fa9ed46`;
- `bro/bundle/ingest_manifest.json`: `df8c08a88fc8ebe9e61c799bf8cd1b10837d5ef6ae38715c3da9ee6918671404`;
- `screen/freatic_prescreen.csv`: `bc46bb6351612d325c08608bd9a3e15cd498781895f899fd36e8866daae17bdc`;
- `screen/vertical_head_pairs.csv`: `11ba0635b2656bab5082b34d7b4b2da99ae0d82e26f748fef217fe3051f861d1`.

## Verdict

**QUALIFIED_BRO_GLD_ROW_ASSESSMENT_CONTRACT**

The upstream quality/provenance defect is corrected and independently exercised by unit tests plus live BRO and live freatic workflows. Rejected and undecided observations are no longer silently promoted into freatic scientific evidence, while their provenance remains retained.

## Mutations

- preserve raw and normalized row-level BRO assessment status in parsed observations;
- report assessment-status counts in ingest provenance;
- add fail-closed scientific evidence selection for fully assessed series;
- apply that selector to Stage-A freatic summaries and vertical-head evidence;
- add regression coverage for approved/rejected/undecided/missing status;
- correct one stale synthetic fixture to state explicitly that its synthetic rows are approved.

## Exclusions retained

Do not:

- delete rejected/undecided rows from acquisition provenance;
- treat missing row status as approved;
- repair or interpolate rejected observations;
- introduce a numeric quality score;
- infer hydraulic continuity from this quality correction;
- enable `ADMISSIBLE_FREATIC`;
- alter REGIS or GeoTOP semantics;
- recalibrate LHM;
- expand Stage-B to the full GMW population.

## Next permitted action

Run ordinary CI and the existing live gates on this documentation checkpoint head. If they remain green and `main` is unchanged, update PR #16 and issue #4 and merge atomically.

After merge, resume the bounded positive Stage-B qualification with `GMW000000020760_T1` as the next direct-evidence candidate. Its corrected screen-gap is `0.485 m`, but this remains descriptive evidence only: positive Stage-B admission still requires affirmative support that the screen represents the fluctuating free surface and must not be inferred from proximity alone.
