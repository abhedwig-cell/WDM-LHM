# TS07 checkpoint — freatic monitoring-tube screening

Status: **QUALIFIED_STAGE_A_REAL_DATA**

Date: 2026-09-16

Canonical branch under review: `work/freatic-screening-qualification`

> **Supersession note, 2026-09-17.** The original qualification remains historical evidence for the Stage-A design and for the 4037/4074/4104 cases. A later qualified BRO row-assessment contract showed that five newer high-frequency `fully_assessed` series contained row-level `afgekeurd` and `onbeslist` values that the original parser did not retain. Their empirical summaries are superseded by `BRO_GLD_ASSESSMENT_STATUS_CHECKPOINT.md`. The 4074 and 4104 numerical evidence below is unchanged by that correction.

## Capability

TS07 provides a conservative two-stage screening framework for selecting BRO monitoring tubes for use in WDM/LHM comparison.

Stage A is an automated BRO-only pre-screen. It may route a tube as:

- `CANDIDATE_FREATIC`
- `REVIEW_DEEP_OR_AMBIGUOUS`
- `INSUFFICIENT_DATA`
- `NOT_USABLE_SERIES`

Stage A does **not** establish that a tube measures the freatic groundwater table.

Stage B final admission remains fail-closed and requires positive hydrogeological / observational evidence. No automatic `ADMISSIBLE_FREATIC` claim is admitted by this checkpoint.

## Scientific decisions

1. The historical 5 m screen-bottom rule is retained only as a provenance-labelled Stage-A review signal (`legacy_gd_depth_risk`). It is not a physical definition of freatic suitability.
2. Parsed GLD time-value pairs, not the PDOK `number_of_observations` catalogue field, determine time-series sample count. In BRO, one Observatie entity can represent a complete time-measurement-value series.
3. Same-GMW multi-filter head differences are preserved as evidence of vertical head structure. No universal threshold for an acceptable vertical gradient is introduced.
4. Missing hydrogeological evidence remains missing; it is never silently interpreted as favourable.

## Synthetic qualification

CI on Python 3.10 and 3.12: **PASS**.

Qualification suite: **23/23 tests PASS**.

The suite includes:

- shallow-candidate routing;
- deep/ambiguous review routing;
- fail-closed missing geometry / short record handling;
- multi-filter vertical-head evidence calculation;
- Stage-B fail-closed admission semantics;
- BRO compact-CSV parsing;
- regression test proving that BRO catalogue Observatie counts are not measurement-point counts.

## Live real-data qualification

GitHub Actions workflow: `Freatic prescreen live smoke`

Qualified run: `35109465960`

Artifact: `10452120627`

Study bbox (CRS84): `5.60,51.94,5.75,52.02`

BRO ingest result:

- GMW objects: 280
- monitoring tubes: 374
- GLD objects: 530
- selected fully assessed series: 10
- stations: 10
- parsed time-value observations: **254,360**
- ingest failures: **0**

TS07 Stage-A result:

- `CANDIDATE_FREATIC`: **5**
- `REVIEW_DEEP_OR_AMBIGUOUS`: **5**
- vertical-head pairs with evidence: **2**

No tube was automatically admitted as freatic.

## Key live cases

### GMW000000004074

Tube 1:

- screen: 2.21–5.21 m below ground level;
- empirical groundwater-depth q05/q50/q95: 2.246 / 2.580 / 2.794 m below ground level;
- Stage A: `REVIEW_DEEP_OR_AMBIGUOUS` because screen bottom is just beyond the historical 5 m criterion.

Tube 2:

- screen: 11.09–11.59 m below ground level;
- Stage A: `REVIEW_DEEP_OR_AMBIGUOUS`.

Same-GMW vertical-head evidence, Tube 1 minus Tube 2:

- overlapping daily values: 418;
- overlap span: 7014 days;
- median head difference: **+0.27 m**;
- robust sigma of difference: **0.133 m**;
- positive sign fraction: **0.981**;
- daily head correlation: **0.792**.

Interpretation: the two filters do not represent one interchangeable hydraulic head. The shallow filter is substantially more plausible as a freatic candidate than the deeper filter, but its long screen extends below the empirical fluctuation envelope. It therefore remains a review case rather than an automatically admitted freatic observation.

This case also demonstrates why a hard 5 m rule cannot be the final admission criterion: the shallow filter barely fails the historical threshold while its upper screen edge lies close to the observed fluctuation zone.

### GMW000000004104

Tube 1:

- screen: 12.02–14.02 m below ground level;
- empirical groundwater-depth q05/q50/q95: 2.739 / 3.224 / 3.620 m below ground level.

Tube 2:

- screen: 35.98–37.98 m below ground level.

Same-GMW vertical-head evidence, Tube 1 minus Tube 2:

- overlapping daily values: 772;
- overlap span: 12692 days;
- median head difference: **+0.12 m**;
- robust sigma of difference: **0.104 m**;
- positive sign fraction: **0.937**;
- daily head correlation: **0.922**.

Interpretation: both filters are far below the observed groundwater-fluctuation zone and show a persistent vertical head difference. They are not admitted as freatic observations.

## Verdict

**TS07 Stage A is qualified for real-data candidate routing.**

The live evidence supports the design boundary:

- automated pre-screening is useful and reproducible;
- the legacy depth rule is useful only as a review signal;
- multi-filter data expose vertical hydraulic structure that a single GLD series cannot reveal;
- final freatic admission must remain a separate Stage-B decision.

## Exclusions

This checkpoint does not admit:

- automatic `ADMISSIBLE_FREATIC` classification;
- a universal vertical-head-difference threshold;
- hydrogeological interpretation from screen depth alone;
- use of Stage-A candidates as independent WDM validation data without lineage audit;
- WDM-conditioned transient correction or LHM recalibration.

## Next permitted action

Define and qualify Stage-B freatic admission using additional hydrogeological evidence, preferably including lithostratigraphy / confining-layer context and same-location multi-filter evidence where available. Stage-B must preserve the fail-closed boundary and be evaluated on known cases before use in the real LHM pilot.
