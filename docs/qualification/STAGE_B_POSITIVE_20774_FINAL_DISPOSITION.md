# Stage-B positive candidate 20774 — final disposition

## Capability

`STAGE_B_POSITIVE_ADMISSION_20774_FINAL_DISPOSITION`

## Phase

`CLOSE`

## Canonical dependency

Canonical `main` at start of this disposition:

`55b8c09b4b6c036cb6feeda33af7746dcf32a146`

This includes:

- PR #10: bounded Stage-B adjudication contract;
- PR #11: bounded positive-candidate REGIS context for `GMW000000020774_T1`;
- PR #12: bounded local BHR-G acquisition;
- PR #13: bounded GeoTOP acquisition and structural parsing;
- PR #14: GeoTOP 1.6.1 codebook-authority qualification.

## Candidate

`GMW000000020774_T1`

Reused direct evidence from qualified TS07 material:

- tube status: `gebruiksklaar`;
- tube in use: yes;
- one registered monitoring tube at the GMW;
- 31,704 fully assessed observations across 4,629 days;
- empirical groundwater-depth q05/q50/q95: `1.498 / 1.812 / 2.054 m-mv`;
- screen: `3.330–4.330 m-mv`;
- screen top is approximately `1.276 m` below q95.

Stage-A candidacy is therefore not sufficient positive Stage-B evidence by itself.

## Reused qualification evidence

### Stage-B adjudication contract

PR #10 admitted the fail-closed qualitative decision contract. Positive `ADMISSIBLE_FREATIC` remains disabled unless separately qualified positive local evidence establishes the required conditions.

### Bounded REGIS context

PR #11 verdict:

`QUALIFIED_REGIS_CONTEXT_POSITIVE_ADMISSION_NOT_ESTABLISHED`

Four fixed REGIS cells around 20774 showed stable regional geometry, but affirmative hydraulic continuity between the observed free-surface support and the monitoring screen was not established. Absence of a second monitoring tube is not positive continuity evidence.

### Local BHR-G evidence

PR #12 qualified a 0.5 km local BHR-G search. The live result was:

`NO_LOCAL_BHRG_FOUND`

This is an evidence-availability boundary only. It is not evidence that a separating interval is absent and does not support positive freatic admission.

### GeoTOP structural evidence

PR #13 qualified metadata, coordinate mapping, one-column acquisition and structural parsing for the 20774 location. Class codes remained uninterpreted pending explicit version-compatible authority.

### GeoTOP semantic authority

PR #14 final verdict:

`PARTIAL_OR_AMBIGUOUS_AUTHORITY`

The bounded official GeoTOP 1.6.1 authority chain did not establish an exact/current semantic codebook applicable to all observed `strat` and `lithok` codes. Therefore:

- admitted operational `lithok` mappings: none;
- admitted operational `strat` mappings: none;
- `lithok=0` remains unknown;
- observed `strat=1000,3030,3100,4100,5000,5120` remain unknown;
- no GeoTOP class meaning may be used to establish hydraulic continuity.

## Formal adjudication

Positive Stage-B admission requires affirmative evidence, not merely absence of contradictory evidence.

For `GMW000000020774_T1`, the qualified evidence establishes:

- a long, usable direct groundwater series;
- valid local construction metadata;
- a screen deeper than the empirical fluctuation support;
- stable regional geological context in the bounded sensitivity set;
- no usable local BHR-G object in the fixed search window;
- no version-qualified GeoTOP semantic mapping that can prove local hydraulic continuity.

It does **not** establish affirmative local hydraulic continuity between the observed free-surface support and the screen.

Therefore the positive rule for `ADMISSIBLE_FREATIC` is not satisfied.

## Verdict

`POSITIVE_ADMISSION_NOT_ESTABLISHED_FAIL_CLOSED`

`GMW000000020774_T1` is **not admitted as `ADMISSIBLE_FREATIC`** on the currently qualified evidence.

This is not a claim that the tube is physically non-freatic. It is a qualification result: the evidence needed for clean independent positive Stage-B admission has not been established.

The appropriate Stage-B state remains fail-closed. No automatic positive admission is enabled.

## Mutations

Documentation-only final disposition. No production logic, thresholds, code mappings, evidence values or adjudication semantics are changed.

## Exclusions retained

Do not:

- continue public GeoTOP source chasing merely to force a semantic classification;
- infer local hydraulic continuity from REGIS or GeoTOP layer codes alone;
- convert unknown class meaning to `no` or to missing;
- introduce a universal `c`, `kv`, head-difference or screen-depth threshold;
- use REGIS `freatisch` or lineage-coupled `kD` as independent LHM-validation evidence;
- infer continuity from absence of a second tube or absence of a BHR-G object;
- recalibrate LHM or build WDM-conditioned corrections;
- expand this disposition to the full GMW population.

## Falsification / reopen condition

This candidate may be reopened only if genuinely new local evidence becomes available that can independently test hydraulic connection across the interval between the observed groundwater-fluctuation support and the screen, for example:

- a local borehole/lithological record tied sufficiently closely to the GMW;
- an exact version-qualified GeoTOP reference-list delivery that materially resolves the observed column semantics;
- another independent local hydrogeological observation capable of testing vertical continuity.

New evidence must be acquired and qualified separately before changing the adjudication.

## Next permitted action

Keep issue #4 open. The overall Stage-B goal still requires at least one genuinely positive local qualification case before automatic positive admission can be enabled.

The next workunit may select another pre-existing Stage-A `CANDIDATE_FREATIC` case from immutable TS07 evidence, but must apply the same positive-evidence rule and must not weaken the adjudication contract to manufacture a positive case.
