# Stage-B positive admission case 20774 checkpoint

Status: **QUALIFIED_REGIS_CONTEXT_POSITIVE_ADMISSION_NOT_ESTABLISHED**

Date: 2026-09-17

## Capability

`STAGE_B_POSITIVE_ADMISSION_CASE_20774`

Phase: QUALIFY boundary reached. This checkpoint qualifies the bounded REGIS context acquisition/geometry capability for one positive Stage-B candidate. It does **not** qualify `GMW000000020774_T1` as `ADMISSIBLE_FREATIC`, does not enable `allow_admissible=True`, and does not change the admitted Stage-B adjudication operator.

## Canonical and branch state

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start and through first live qualification: `f711466bb49d01bf5d083897456fbdd07315b8a0`
- branch: `work/stage-b-positive-admission-20774`
- design checkpoint: `d65881ec00a743fc9d927bc3bec5952b588ac321`
- qualified implementation head: `fcec8c41baade3e15d4d666e30eaccab4b6ca66c`
- PR: `#11`
- parent capability: `STAGE_B_FREATIC_ADJUDICATION`
- parent verdict: `QUALIFIED_STAGE_B_ADJUDICATION_CONTRACT`

## Reused immutable evidence

### TS07 direct evidence

Reused without broad BRO/PDOK reacquisition:

- workflow run `35109465960`;
- artifact `10452120627`, `freatic-smoke-35109465960`;
- artifact digest SHA-256 `b4770757f27d5bbd0e7e290bcfa187c3affb6f444293e0c83b22c7c4b90098f0`.

Selected candidate `GMW000000020774_T1`:

- GMW `GMW000000020774`;
- GLD `GLD000000007466`;
- BRO ground level `9.85 m NAP`;
- RD approximately `x=172274.997571`, `y=447781.978030`;
- tube status `gebruiksklaar`;
- tube in use `ja`;
- exactly one registered monitoring tube in the qualified TS07 bundle;
- screen `3.330–4.330 m-mv`, or `6.520–5.520 m NAP`;
- series class `fully_assessed`;
- `31,704` observations over `4,629` days;
- empirical groundwater-depth q05/q50/q95 `1.498 / 1.812 / 2.054 m-mv`;
- above-ground fraction `0.0`;
- screen top lies about `1.276 m` deeper than q95.

Stage-A `CANDIDATE_FREATIC` is not treated as positive Stage-B evidence by itself.

### Qualified REGIS coordinate authority

Reused from:

- workflow `35132157424`;
- artifact `10461443564`;
- artifact digest SHA-256 `4c21531c95ee9fc1870fbf4ad34ed6d7e8eac5be75c061afd39788675eb2e405`;
- raw coordinate SHA-256 `fa39271a98fefa2091483b7247d53e3744e1e26e478969310ce6f3560725c7f3`.

Explicit-bound mapping for the selected location gives nominal REGIS cell `(1722,1477)`. The bounded positive-case sensitivity set is:

1. nominal `(1722,1477)`;
2. east `(1723,1477)`;
3. north `(1722,1478)`;
4. north-east `(1723,1478)`.

The four columns are compared side by side and never averaged.

### REGIS file/property semantics

The already qualified package authority in `STAGE_B_REGIS_DOCUMENT_AUTHORITY.md` is reused. It admits:

- `top` / `bottom` geometry semantics;
- `kh` as horizontal conductivity in m/day;
- `kv` as vertical conductivity in m/day;
- `c` as resistance in days.

It does not by itself make any REGIS layer a local truth or establish local hydraulic continuity.

## New implementation

Implementation head `fcec8c41baade3e15d4d666e30eaccab4b6ca66c` adds:

- `src/wdm_lhm/regis_positive_case_20774.py`;
- `src/wdm_lhm/regis_positive_case_20774_cli.py`;
- `tests/test_regis_positive_case_20774.py`;
- `.github/workflows/regis-positive-20774.yml`.

The capability:

- requests only the four fixed cells above;
- requests exactly `top`, `bottom`, `kh`, `kv`, `c` for 132 layers;
- excludes `freatisch`, `kD`, `hgv`, `sdh`, `sdv`;
- preserves raw response hashes;
- maps only exact raw `-9999` to null;
- performs no imputation;
- compares geometry without averaging cells;
- carries raw `kh`/`kv`/`c` values without applying thresholds;
- does not infer hydraulic semantics from layer codes alone;
- hard-fails the positive-admission boundary by keeping `hydraulic_continuity_established=false` and `admissible_freatic_assigned=false`.

## Qualification tests

Ordinary CI run `35184727204`: **PASS** on exact implementation head `fcec8c41baade3e15d4d666e30eaccab4b6ca66c`.

- Python 3.10.21: **75 passed**;
- Python 3.12.14: **75 passed**.

Live bounded context run `35184727312`: **PASS** on the same head.

Artifact:

- ID `10481622733`;
- name `stage-b-positive-20774-35184727312`;
- artifact digest SHA-256 `c2a8489297ff6fd55aa152e7fb79fcce4396b674c1c67bea3a11f28b2aff0feb`.

Derived evidence hashes:

- raw manifest SHA-256 `733e61ccfd92544fd644a94584c08fefb93c1264e61ebe0bb03eb522d0cc6309`;
- parsed JSON SHA-256 `47ba60759eec0e5c6bfc972bd65dc83c83f9d10740222675c285908625f8e34c`;
- geometry JSON SHA-256 `7f280cb3b53358cb2f861fa4cc3635bd2ca207f6ac279b60dd8e61be7abd8517`.

Raw column SHA-256:

- nominal: `8eb25bc7972deacc302a134b4b26c7ad90049650c3f9ebf59680ec930a1e0231`;
- east: `02952bcffeda02531f67bbe875e58e7dc36a17fde3f1e3c3666d10bfcdcaf09d`;
- north: `0bbd494a7ee703abe1a681b259f0c5dfbdbd3848564867e148538cccc34bd8d8`;
- north-east: `8664c668002933b3180bc70b59de8c1a74523fe0b5b9656cd0999157d10a1d23`.

For every column the parser found 132 labels with the same present-value counts: top `27`, bottom `26`, kh `17`, kv `10`, c `10`.

## Live scientific result

The q95 elevation is `7.796 m NAP`. The monitoring screen is `6.520–5.520 m NAP`.

Across all four bounded REGIS columns, the interval from q95 support down through the screen has the same layer sequence:

`NUBXz2 -> NUBXk1`

The screen itself also crosses the same two-layer sequence in all four cells.

The geometry is therefore regionally stable over this bounded four-cell sensitivity set. It is not the kind of 100 m cell-instability observed for 4074.

The raw hydraulic-property context for the lower interval is also similar across the four columns:

- `NUBXk1` vertical conductivity `kv` approximately `0.00501–0.00504 m/day`;
- `NUBXk1` resistance `c` approximately `152.74–167.74 days`.

These values may be reported because their units/variable meanings are package-qualified. They are **not** converted into a universal confining-layer threshold or an automatic hydraulic classification.

## Scientific adjudication boundary

This REGIS evidence does not provide the positive evidence required to set `VerticalHydraulicInterpretation.NO_DISTINCT_REGIME_EVIDENCE` or to declare hydraulic continuity from the empirical free-surface support to the monitoring screen.

Reasons:

1. the selected screen lies materially below the observed fluctuation support rather than directly within it;
2. absence of a second GMW tube is not affirmative continuity evidence;
3. REGIS shows a stable change of regional unit geometry between the q95 support and the screen rather than a single uninterrupted interval;
4. a resistance-bearing / low-`kv` regional interval is present in the same bounded context, but no qualified universal `c` or `kv` threshold exists that would justify converting this regional model value into exact local separation or connection;
5. REGIS remains a 100 x 100 m regional model and cannot establish local well-scale hydraulic connection by itself.

Therefore a positive conclusion cannot be manufactured by treating regional stability as local continuity.

## Verdict

**QUALIFIED_REGIS_CONTEXT_POSITIVE_ADMISSION_NOT_ESTABLISHED**

For `GMW000000020774_T1`:

- direct observations: `AVAILABLE`;
- time-series usability: supported;
- construction metadata: `AVAILABLE` for required Stage-B fields;
- same-GMW multi-filter evidence: `NOT_APPLICABLE` in the qualified bundle;
- bounded REGIS geometry: spatially stable;
- local hydraulic continuity: **NOT ESTABLISHED**;
- Stage-B outcome remains fail-closed and must not be promoted to `ADMISSIBLE_FREATIC`;
- validation-lineage eligibility is not reached because the hydraulic admission gate is not passed.

This is a negative result for the attempted positive qualification, but a successful qualification of the scientific boundary: REGIS alone is insufficient for this candidate.

## Mutations

Only candidate-specific evidence machinery and this checkpoint are changed. The admitted generic Stage-B adjudication operator is untouched.

## Exclusions retained

- no expansion to all GMWs;
- no broad BRO rediscovery;
- no LHM recalibration or WDM-conditioned correction;
- no residual regionalisation;
- no numeric adjudication score;
- no universal screen-depth, head-difference, `c`, `kv`, or boundary-distance threshold;
- no neighbouring-cell averaging;
- no hydraulic interpretation from layer codes alone;
- no missing-value imputation;
- no use of REGIS `freatisch` or lineage-coupled `kD` as independent LHM-validation evidence;
- no production `allow_admissible=True`.

## Next permitted action

Do **not** deepen REGIS interpretation for this case merely to force a positive outcome.

The next scientific decision surface is a bounded local higher-resolution evidence workunit for `GMW000000020774` only. Prefer direct/local evidence capable of testing whether the interval between the observed fluctuation zone and the screen is hydraulically continuous, for example:

1. local BRO borehole/lithological information at or immediately adjacent to the monitoring well, if available; otherwise
2. GeoTOP/local high-resolution geological context, explicitly treated as supporting rather than point truth.

Acquisition and interpretation must remain separate. If no sufficiently local evidence exists, the candidate remains `REVIEW_REQUIRED` / not positively admitted. Do not switch to another candidate merely to obtain a positive result until this falsification path is closed.