# Stage-B freatic adjudication — qualification and falsification cases

Status: **DESIGN_QUALIFICATION_ORACLE**

Date: 2026-09-17

This document fixes the currently qualified real-data evidence that any later implementation must satisfy. It does not itself implement an automatic classifier.

## Dependencies

Canonical source state before this workunit:

- main merge SHA: `fabbace765c34cf04a99267b55be908f83c58fde`;
- TS07 checkpoint: `docs/qualification/TS07_CHECKPOINT.md`, status `QUALIFIED_STAGE_A_REAL_DATA`;
- REGIS geometry checkpoint: `docs/qualification/STAGE_B_REGIS_SCREEN_OVERLAP.md`, status `QUALIFIED_GEOMETRY_ONLY_REAL_DATA`;
- parsed REGIS hydro JSON SHA-256: `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`;
- geometry workflow run: `35181574136`, PASS;
- geometry artifact: `10480936971`;
- geometry artifact digest: `a14fae5625735623da63ba37267ccd46b07a8534976875088f956559a2062391`.

No REGIS reacquisition is required for this design workunit while these dependencies remain unchanged.

## Case Q1 — GMW000000004104 Tube 1

Direct evidence:

- BRO ground level: 9.81 m NAP;
- screen: 12.02–14.02 m below ground;
- empirical groundwater-depth q05/q50/q95: 2.739 / 3.224 / 3.620 m below ground.

Same-location evidence with Tube 2:

- 772 overlapping daily values;
- median Tube1–Tube2 head difference: +0.12 m;
- robust sigma: 0.104 m;
- positive sign fraction: 0.937;
- correlation: 0.922.

REGIS geometry:

- full 2.00 m screen in `NUgsc`;
- REGIS ground-level diagnostic about +1.34 m relative to BRO ground level.

Required qualification outcome:

- MUST NOT produce `ADMISSIBLE_FREATIC`;
- intended current state: `NOT_ADMISSIBLE_FREATIC`;
- REGIS geometry may support context but is not required to reach the safety conclusion.

Falsification condition: any rule that admits this tube because its head series is coherent or because one REGIS unit appears hydraulically plausible fails qualification.

## Case Q2 — GMW000000004104 Tube 2

Direct/construction evidence:

- screen: 35.98–37.98 m below ground;
- screen elevation: -26.17 to -28.17 m NAP.

Same-location evidence is the same Q1 pair evidence above.

REGIS geometry:

- full 2.00 m screen in `NUPZ-WAz1`.

Required qualification outcome:

- MUST NOT produce `ADMISSIBLE_FREATIC`;
- intended current state: `NOT_ADMISSIBLE_FREATIC`.

Falsification condition: a deep filter cannot become freatic merely because a regional layer code is interpreted favourably.

## Case Q3 — GMW000000004074 Tube 1

Direct evidence:

- BRO ground level: 7.93 m NAP;
- screen: 2.21–5.21 m below ground;
- empirical groundwater-depth q05/q50/q95: 2.246 / 2.580 / 2.794 m below ground.

Same-location evidence with Tube 2:

- 418 overlapping daily values;
- median Tube1–Tube2 head difference: +0.27 m;
- robust sigma: 0.133 m;
- positive sign fraction: 0.981;
- correlation: 0.792.

REGIS sensitivity:

- monitoring coordinate about 0.0056 m east of the nominal cell's western boundary;
- nominal screen overlap: `NUBXz3 -> NUBXz4 -> NUgsc`, approximately 0.69 / 1.07 / 1.24 m;
- west-neighbour overlap: full 3.00 m in `NUgsc`.

Required qualification outcome:

- current evidence MUST remain `REVIEW_REQUIRED`;
- the record MAY state that Tube 1 is a more plausible freatic candidate than Tube 2;
- that relative statement MUST NOT be transformed into `ADMISSIBLE_FREATIC`;
- the two REGIS columns MUST remain separate sensitivity alternatives.

Falsification conditions:

- admission solely because Tube 1 is the shallower filter;
- admission solely because its upper screen edge is near the empirical fluctuation zone;
- resolving REGIS uncertainty by averaging the two columns;
- allowing REGIS to overrule the direct multi-filter evidence.

## Case Q4 — GMW000000004074 Tube 2

Construction evidence:

- screen: 11.09–11.59 m below ground;
- screen elevation: -3.16 to -3.66 m NAP.

Same-location evidence is the Q3 pair evidence above.

REGIS geometry:

- full 0.50 m screen in `NUgsc` in both nominal and west-neighbour columns.

Required qualification outcome:

- MUST NOT produce `ADMISSIBLE_FREATIC`;
- intended current state: `NOT_ADMISSIBLE_FREATIC` because the deep screen is hydraulically distinct from the shallower candidate under persistent same-location head separation.

Falsification condition: agreement of the two REGIS columns for this screen is not sufficient positive local evidence for freatic admission.

## Global invariants

Any later implementation must satisfy all of the following:

1. direct local evidence outranks REGIS context;
2. positive support is required for `ADMISSIBLE_FREATIC`;
3. missing evidence remains missing;
4. contradictory or spatially unstable evidence fails closed;
5. no universal head-difference threshold is introduced implicitly;
6. no 4074 neighbour averaging occurs;
7. BRO ground level remains the screen-elevation authority;
8. `freatisch` and lineage-coupled `kD` remain excluded as independent LHM-validation evidence;
9. physical freatic adjudication remains separate from validation-lineage eligibility.
