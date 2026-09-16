# Live BRO qualification evidence

Date: 2026-09-16

## Verdict

**TS06 technical live ingest: PASS.**

This verdict qualifies the technical route from the public PDOK/BRO services to the WDM-LHM observation bundle. It does **not** qualify the automatically selected monitoring tubes as representative freatic validation wells, and it does not establish independence from WDM or LHM calibration data.

## GitHub Actions evidence

- PR: #1 `Bootstrap Status A-light WDM-LHM research software`
- qualified head SHA: `80cceb0fa1dd5ca5dddaa9cf569c999c2cac719c`
- workflow: `BRO live smoke`
- run ID: `35105889506`
- artifact ID: `10449838041`
- bbox CRS84: `5.60,51.94,5.75,52.02`
- maximum downloaded GLD series in smoke: 2

Functional smoke gate required `selected_series > 0`, `observations > 0`, and `failures == 0`.

## Live counts

| Item | Count |
| --- | ---: |
| GMW objects | 280 |
| monitoring tubes | 374 |
| GLD objects | 530 |
| selected GLD series | 2 |
| station/tube supports | 2 |
| parsed observations | 126,578 |
| ingest failures | 0 |

The two fully assessed series contained 19,547 and 107,031 observations respectively.

## Important finding from the first live attempt

The first network-successful run exposed a real service-contract difference: the current compact GLD CSV can be returned without a header. The original parser deliberately failed closed instead of guessing column meaning, resulting in zero parsed observations and two recorded failures.

The parser was then extended with a conservative positional route that accepts a headerless compact response only when column 1 overwhelmingly validates as timestamps and column 2 as numeric groundwater levels. A regression test was added using the verified live structure. The strengthened smoke workflow now fails on empty or partial ingestion.

## Physical-suitability boundary

The two smoke-selected tubes are not automatically admitted as freatic validation wells.

- `GMW000000004104_T1`: ground level 9.81 m NAP, screen top -2.210 m NAP, screen bottom -4.210 m NAP. Approximate screen depth: 12.02–14.02 m below ground level.
- `GMW000000020760_T1`: ground level 14.96 m NAP, screen top 12.023 m NAP, screen bottom 11.023 m NAP. Approximate screen depth: 2.94–3.94 m below ground level.

These examples show that record length alone is insufficient. Freatic suitability, filter position, head plausibility, local hydrogeology and lineage must be screened before observations enter TS01–TS04 as validation evidence.

## Next permitted action

Define and qualify a transparent freatic-monitoring-tube screening/admission step. Do not introduce an arbitrary screen-depth threshold as a hidden ingest rule; first document the hydrological rationale and how exceptions such as confined/artesian conditions are handled.
