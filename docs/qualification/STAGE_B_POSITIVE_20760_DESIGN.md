# Stage-B positive candidate 20760 — design checkpoint

Status: **DESIGN_LOCAL_EVIDENCE_ACQUISITION_REQUIRED**

Date: 2026-09-17

## Capability

`STAGE_B_POSITIVE_ADMISSION_20760`

## Phase

`ACQUIRE` design boundary.

## Canonical and branch state

- repository: `abhedwig-cell/WDM-LHM`;
- canonical `main`: `1c276b408eda795ed7cea595e29396eb4cc4e380`;
- branch: `work/stage-b-positive-20760`;
- branch start: `1c276b408eda795ed7cea595e29396eb4cc4e380`;
- parent capability: `STAGE_B_FREATIC_ADJUDICATION`;
- parent verdict: `QUALIFIED_STAGE_B_ADJUDICATION_CONTRACT`.

No broad repository recovery or new Stage-B decision semantics are permitted in this workunit.

## Reused immutable direct evidence

Source qualification:

- freatic live workflow run: `35216362746`;
- artifact: `10495082246`;
- artifact digest: `eeb19fd1684b344686d2ac72bc14f95e8c01c7fe248162b9ad9e3d43b64cdab8`;
- `bro/bundle/observations.csv` SHA-256: `59b69315a9d6841a3d639e56550d546810f9b6451d282e4894864e424fa9ed46`;
- `bro/bundle/stations.csv` SHA-256: `9c7c81960db9d3a3d7010fbee547f3d18e28bd4286813ad2064bacdd51580e1d`;
- `screen/freatic_prescreen.csv` SHA-256: `bc46bb6351612d325c08608bd9a3e15cd498781895f899fd36e8866daae17bdc`.

Selected candidate:

`GMW000000020760_T1`

Qualified station/construction record:

- GMW: `GMW000000020760`;
- GLD: `GLD000000007463`;
- RD: `x=174493.003818`, `y=446332.971183`;
- BRO ground level: `14.960 m NAP`;
- tube status: `gebruiksklaar`;
- tube in use: `ja`;
- one registered monitoring tube in the qualified TS07 bundle;
- screen top: `12.023 m NAP` = `2.937 m-mv`;
- screen bottom: `11.023 m NAP` = `3.937 m-mv`.

Corrected row-assessment evidence:

- raw observations: `107,031`;
- admitted `goedgekeurd`: `103,976`;
- rejected: `2,947`;
- undecided: `108`;
- admitted record span: `4,617` days, 2012-12-06 through 2025-07-29;
- q05/q50/q95 groundwater depth: `1.162 / 1.940 / 2.452 m-mv`;
- minimum admitted depth: `0.679 m-mv`;
- maximum admitted depth: `2.592 m-mv`;
- admitted observations reaching the screen top at `2.937 m-mv`: `0`;
- screen-top minus q95: `+0.485 m`;
- Stage-A routing: `CANDIDATE_FREATIC`.

The earlier apparent above-ground block is not admitted scientific evidence because BRO marks those rows non-approved.

## Scientific interpretation boundary

The direct record is strong enough to establish:

- usable direct observations;
- valid construction metadata;
- a long high-frequency head record;
- no same-GMW peer-filter contradiction in the qualified bundle.

It is **not** sufficient by itself to establish `ScreenRelation.SUPPORTS_FREE_SURFACE` or `VerticalHydraulicInterpretation.NO_DISTINCT_REGIME_EVIDENCE`.

The critical reason is physical rather than statistical: throughout the admitted record the measured head remains above the filter top. A saturated screen below the observed water table can represent the unconfined aquifer, but that requires affirmative local hydraulic/geological continuity evidence. The `0.485 m` q95 gap is descriptive evidence only and must not become a new threshold.

The failed positive case `GMW000000020774_T1` is retained as a falsification precedent: regional REGIS stability and absence of a second tube are not positive continuity evidence.

## Next acquisition

Acquire bounded local BRO BHR-G evidence around the exact 20760 coordinate using the already qualified `bhrg_local_acquisition` engine.

Acquisition rules:

- fixed candidate `GMW000000020760_T1` only;
- fixed 0.5 km discovery window, retained as an acquisition window and not a scientific threshold;
- raw BHR-G discovery/object acquisition only;
- no lithology interpretation in the acquisition step;
- no hydraulic interpretation;
- no screen correlation;
- no GeoTOP or REGIS fallback inside this step;
- no admission decision;
- `allow_admissible` remains disabled.

A small candidate adapter may parameterize the already qualified acquisition engine. Do not fork or rewrite the network/acquisition architecture.

## Decision after acquisition

- if no local BHR-G object exists, record the evidence-availability boundary and keep positive admission fail-closed;
- if one or more local objects exist, persist raw hashes first, then open a separate interpretation phase limited to whether the interval from the observed head support to the screen contains affirmative local evidence for or against hydraulic continuity;
- do not infer continuity from absence of a coded confining unit unless the source semantics and local relation are independently qualified.

## Exclusions

Do not:

- enable `ADMISSIBLE_FREATIC` from screen proximity alone;
- reuse the historical 5 m rule as physics;
- create a numeric admission score;
- repeat the 20774 REGIS/GeoTOP chase merely to obtain a positive case;
- average regional cells;
- impute unknown evidence;
- use `freatisch` or lineage-coupled `kD` as independent validation evidence;
- recalibrate LHM or build WDM-conditioned corrections;
- expand to the full GMW population.

## Next permitted action

Implement the bounded 20760 BHR-G acquisition adapter and PR-triggered live qualification. Persist the live result before any lithological or hydraulic interpretation.