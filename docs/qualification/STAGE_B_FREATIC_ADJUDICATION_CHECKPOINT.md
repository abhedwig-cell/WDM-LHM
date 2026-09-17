# Stage-B freatic adjudication checkpoint

Status: **DESIGN_READY_FOR_QUALIFICATION**

Date: 2026-09-17

## Capability

`STAGE_B_FREATIC_ADJUDICATION`

Phase: DESIGN / pre-implementation qualification.

## Canonical source

- canonical main at workunit start: `fabbace765c34cf04a99267b55be908f83c58fde`;
- branch: `work/stage-b-freatic-adjudication`;
- branch started exactly from canonical main after PR #9 merge.

## Reused immutable evidence

- TS07 Stage A: `QUALIFIED_STAGE_A_REAL_DATA`;
- GMW000000004074 direct and same-GMW multi-filter evidence from `docs/qualification/TS07_CHECKPOINT.md`;
- GMW000000004104 direct and same-GMW multi-filter evidence from the same checkpoint;
- REGIS v02r2s3 package identity and 100 x 100 m support;
- qualified parsed hydro JSON SHA-256: `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`;
- qualified geometry workflow `35181574136`, artifact `10480936971`, digest `a14fae5625735623da63ba37267ccd46b07a8534976875088f956559a2062391`;
- explicit 4074 nominal/west-neighbour sensitivity;
- BRO ground level authority for screen elevations.

No live REGIS acquisition was repeated.

## Design changes

The Stage-B documentation now fixes:

- explicit evidence precedence: direct observations -> same-location multi-filter -> construction metadata -> regional hydrogeological context -> legacy heuristics;
- four hydraulic adjudication states: `ADMISSIBLE_FREATIC`, `NOT_ADMISSIBLE_FREATIC`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`;
- positive evidence requirements for `ADMISSIBLE_FREATIC`;
- fail-closed treatment of contradiction, scale sensitivity and unknown evidence;
- formal separation of physical freatic adjudication from LHM-validation lineage independence;
- 4074/4104 qualification and falsification cases;
- continued exclusion of REGIS `freatisch` and lineage-coupled `kD` as independent validation evidence.

No numeric score, universal vertical-head threshold or production classifier is introduced.

## Qualification oracle

`docs/qualification/STAGE_B_FREATIC_ADJUDICATION_QUALIFICATION.md` fixes the required safety outcomes:

- 4104 Tube 1: not admissible, intended `NOT_ADMISSIBLE_FREATIC`;
- 4104 Tube 2: not admissible, intended `NOT_ADMISSIBLE_FREATIC`;
- 4074 Tube 1: `REVIEW_REQUIRED` under current evidence;
- 4074 Tube 2: not admissible, intended `NOT_ADMISSIBLE_FREATIC`.

The oracle deliberately preserves the statement that 4074 Tube 1 is more plausible than Tube 2 without promoting it to an independently validated freatic observation.

## Verdict

**DESIGN_READY_FOR_QUALIFICATION**

The scientific decision surface is now explicit enough to implement a small evidence-record/adjudication contract without inventing a score.

## Mutations

- created branch `work/stage-b-freatic-adjudication` from canonical main;
- updated Stage-B theory, conceptual model and formal decision model;
- added real-data qualification/falsification oracle;
- added this resumable checkpoint.

## Exclusions

This checkpoint does not permit:

- expansion to all 280 GMWs;
- LHM recalibration or WDM-conditioned correction;
- residual regionalisation;
- automatic use of Stage-A candidates as validation observations;
- hydraulic interpretation from REGIS layer code alone;
- neighbour-column averaging;
- missing-value imputation;
- a numeric adjudication score.

## Next permitted action

Implement the smallest typed evidence-record and qualitative adjudication contract needed to express these states, with tests pinned to the four qualification cases. Production `ADMISSIBLE_FREATIC` must remain disabled unless its positive-evidence path is explicitly exercised by a separately qualified case.
