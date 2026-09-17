# Stage-B freatic adjudication checkpoint

Status: **QUALIFIED_STAGE_B_ADJUDICATION_CONTRACT**

Date: 2026-09-17

## Capability

`STAGE_B_FREATIC_ADJUDICATION`

Phase: QUALIFY complete for the bounded typed adjudication contract. This checkpoint is documentation-only; its resulting branch head must still pass ordinary CI before merge.

## Canonical source

- canonical main at workunit start: `fabbace765c34cf04a99267b55be908f83c58fde`;
- canonical main at qualification reconciliation: `fabbace765c34cf04a99267b55be908f83c58fde`;
- branch: `work/stage-b-freatic-adjudication`;
- design checkpoint commit: `81444df354235063c3fe05066b84d315b55c8eaa`;
- qualified implementation head before this documentation-only checkpoint: `1978854b98a64e60ecc58f062c9f772819d20f84`;
- PR: `#10`.

No relevant main or PR-head drift occurred during qualification.

## Reused immutable evidence

- TS07 Stage A: `QUALIFIED_STAGE_A_REAL_DATA`;
- GMW000000004074 and GMW000000004104 direct/multi-filter evidence from `docs/qualification/TS07_CHECKPOINT.md`;
- REGIS v02r2s3 package identity and 100 x 100 m support;
- qualified parsed hydro JSON SHA-256: `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`;
- qualified geometry workflow `35181574136`, artifact `10480936971`, digest `a14fae5625735623da63ba37267ccd46b07a8534976875088f956559a2062391`;
- explicit 4074 nominal/west-neighbour sensitivity;
- BRO ground-level authority for screen elevations.

No live REGIS acquisition was repeated.

## Admitted scientific contract

The documentation fixes:

- evidence precedence: direct observations -> same-location multi-filter -> construction metadata -> regional hydrogeological context -> legacy heuristics;
- `ADMISSIBLE_FREATIC`, `NOT_ADMISSIBLE_FREATIC`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`;
- positive local evidence requirements for `ADMISSIBLE_FREATIC`;
- fail-closed contradiction, scale-sensitivity and unknown-evidence handling;
- separate hydraulic adjudication and validation-lineage gates;
- four real-data qualification/falsification cases.

Lower-priority REGIS context cannot overrule materially contradictory direct local evidence. GMW000000004074 nominal and west-neighbour columns remain distinct sensitivity alternatives and are never averaged.

## Implementation

`src/wdm_lhm/freatic_adjudication.py` provides:

- typed evidence and output enums/dataclasses;
- qualitative precedence logic only;
- no numeric score;
- no conversion of REGIS layer codes or numerical head differences into unqualified hydraulic meaning;
- default-disabled automatic `ADMISSIBLE_FREATIC` path through `allow_admissible=False`;
- a separate validation-lineage eligibility operator.

`tests/test_freatic_adjudication.py` pins the safety contract for:

- 4104 Tube 1 -> `NOT_ADMISSIBLE_FREATIC`;
- 4104 Tube 2 -> `NOT_ADMISSIBLE_FREATIC`;
- 4074 Tube 1 -> `REVIEW_REQUIRED`;
- 4074 Tube 2 -> `NOT_ADMISSIBLE_FREATIC`;
- unknown required evidence -> `INSUFFICIENT_EVIDENCE`;
- legacy heuristic non-authority;
- local-evidence precedence over regional instability;
- the positive-admission gate;
- separation of hydraulic admission from validation lineage.

## Qualification results

Ordinary GitHub Actions CI on implementation head `1978854b98a64e60ecc58f062c9f772819d20f84`:

- run: `35183509967`;
- conclusion: **PASS**;
- Python 3.10.21: **71 passed** in 6.74 s;
- Python 3.12.14: **71 passed** in 9.18 s;
- both package-install and qualification-test steps: PASS.

The run tested the PR merge ref of implementation head `1978854b98a64e60ecc58f062c9f772819d20f84` into unchanged canonical main `fabbace765c34cf04a99267b55be908f83c58fde`.

## Qualification oracle verdict

- GMW000000004104 Tube 1: `NOT_ADMISSIBLE_FREATIC`;
- GMW000000004104 Tube 2: `NOT_ADMISSIBLE_FREATIC`;
- GMW000000004074 Tube 1: `REVIEW_REQUIRED`;
- GMW000000004074 Tube 2: `NOT_ADMISSIBLE_FREATIC`.

The framework preserves the weaker statement that 4074 Tube 1 is a more plausible freatic candidate than its deeper companion without promoting that statement to `ADMISSIBLE_FREATIC` or to independent LHM-validation eligibility.

## Verdict

**QUALIFIED_STAGE_B_ADJUDICATION_CONTRACT**

The bounded qualitative contract is qualified for the stated adversarial cases. Automatic positive admission remains deliberately disabled by default because no separate positive real-data automatic-admission case has yet been qualified.

## Mutations in this workunit

- created `work/stage-b-freatic-adjudication` from canonical main after PR #9 merge;
- strengthened theory, conceptual evidence hierarchy and formal decision model;
- added real-data qualification/falsification oracle;
- implemented the typed qualitative adjudication contract;
- added pinned tests for the four current real-data cases and guardrails;
- opened PR #10;
- ran and passed ordinary CI on the implementation head;
- persisted this qualification checkpoint.

## Exclusions

This qualification does not permit:

- expansion to all 280 GMWs;
- LHM recalibration or WDM-conditioned correction;
- residual regionalisation;
- a numeric adjudication score;
- a universal vertical-head threshold;
- use of the historical 5 m criterion as a physical admission rule;
- REGIS neighbour averaging;
- hydraulic semantics inferred from REGIS layer code alone;
- replacement of BRO ground level by REGIS ground level for screen elevations;
- missing-value imputation;
- use of `freatisch` or lineage-coupled `kD` as independent validation evidence;
- production automatic `ADMISSIBLE_FREATIC` without a separately qualified positive case.

## Next permitted action

Run ordinary CI on the documentation-only checkpoint head. If PASS and main/head dependencies remain unchanged, update PR #10 and issue #4 with the final qualification evidence and merge PR #10 atomically. After merge, the next separate scientific decision surface is qualification of a positive local `ADMISSIBLE_FREATIC` case, not broad REGIS refinement or expansion to the full GMW population.
