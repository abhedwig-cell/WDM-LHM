# Stage-B freatic adjudication checkpoint

Status: **IMPLEMENTED_PENDING_CI**

Date: 2026-09-17

## Capability

`STAGE_B_FREATIC_ADJUDICATION`

Phase: QUALIFY, implementation prepared; ordinary CI still required on the implementation head.

## Canonical source

- canonical main at workunit start: `fabbace765c34cf04a99267b55be908f83c58fde`;
- branch: `work/stage-b-freatic-adjudication`;
- design checkpoint commit: `81444df354235063c3fe05066b84d315b55c8eaa`.

## Reused immutable evidence

- TS07 Stage A: `QUALIFIED_STAGE_A_REAL_DATA`;
- GMW000000004074 and GMW000000004104 direct/multi-filter evidence from `docs/qualification/TS07_CHECKPOINT.md`;
- REGIS v02r2s3 package identity and 100 x 100 m support;
- qualified parsed hydro JSON SHA-256: `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`;
- qualified geometry workflow `35181574136`, artifact `10480936971`, digest `a14fae5625735623da63ba37267ccd46b07a8534976875088f956559a2062391`;
- explicit 4074 nominal/west-neighbour sensitivity;
- BRO ground-level authority for screen elevations.

No live REGIS acquisition was repeated.

## Design admitted for implementation

The documentation fixes:

- evidence precedence: direct observations -> same-location multi-filter -> construction metadata -> regional hydrogeological context -> legacy heuristics;
- `ADMISSIBLE_FREATIC`, `NOT_ADMISSIBLE_FREATIC`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`;
- positive evidence requirements for admission;
- fail-closed contradiction/scale-sensitivity handling;
- separate hydraulic adjudication and validation-lineage gates;
- four real-data qualification/falsification cases.

## Implementation delta

Added `src/wdm_lhm/freatic_adjudication.py` with:

- typed evidence and output enums/dataclasses;
- no numeric score;
- no conversion of REGIS codes or numerical head differences into hydraulic meaning;
- qualitative precedence logic only;
- default-disabled automatic `ADMISSIBLE_FREATIC` path through `allow_admissible=False`;
- separate validation-lineage eligibility operator.

Added `tests/test_freatic_adjudication.py` with pinned safety tests for:

- 4104 Tube 1 -> `NOT_ADMISSIBLE_FREATIC`;
- 4104 Tube 2 -> `NOT_ADMISSIBLE_FREATIC`;
- 4074 Tube 1 -> `REVIEW_REQUIRED`;
- 4074 Tube 2 -> `NOT_ADMISSIBLE_FREATIC`;
- unknown evidence -> `INSUFFICIENT_EVIDENCE`;
- legacy heuristic non-authority;
- local-evidence precedence over regional instability;
- positive-admission gate;
- separation of hydraulic admission from validation lineage.

## Verdict

**IMPLEMENTED_PENDING_CI**

No production expansion or positive automatic admission is permitted until ordinary repository CI passes on the implementation head.

## Exclusions

- no expansion to all 280 GMWs;
- no LHM recalibration or WDM-conditioned correction;
- no residual regionalisation;
- no score or universal vertical-head threshold;
- no REGIS neighbour averaging;
- no hydraulic semantics inferred from REGIS layer code;
- no missing-value imputation;
- no use of `freatisch` or lineage-coupled `kD` as independent validation evidence.

## Next permitted action

Run ordinary CI on the implementation head. If PASS with unchanged evidence dependencies, persist the CI run/head, update this checkpoint to a qualified verdict, update issue #4, and only then consider merge/admission of this bounded capability.
