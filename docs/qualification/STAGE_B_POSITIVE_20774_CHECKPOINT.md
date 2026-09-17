# Stage-B positive admission case 20774 checkpoint

Status: **DESIGN_POSITIVE_CASE_PENDING_LOCAL_CONTEXT**

Date: 2026-09-17

## Capability

`STAGE_B_POSITIVE_ADMISSION_CASE_20774`

Phase: DESIGN/QUALIFY candidate selection. This checkpoint does not enable automatic `ADMISSIBLE_FREATIC` and does not change the admitted Stage-B adjudication operator.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start: `f711466bb49d01bf5d083897456fbdd07315b8a0`
- branch: `work/stage-b-positive-admission-20774`
- parent capability: `STAGE_B_FREATIC_ADJUDICATION`
- parent verdict: `QUALIFIED_STAGE_B_ADJUDICATION_CONTRACT`

## Reused immutable evidence

TS07 live evidence is reused from:

- workflow run `35109465960`;
- artifact `10452120627` (`freatic-smoke-35109465960`);
- artifact digest SHA-256 `b4770757f27d5bbd0e7e290bcfa187c3affb6f444293e0c83b22c7c4b90098f0`;
- no new broad BRO/PDOK acquisition is performed in this phase.

Qualified REGIS coordinate evidence is reused from:

- workflow `35132157424`;
- artifact `10461443564`;
- artifact digest SHA-256 `4c21531c95ee9fc1870fbf4ad34ed6d7e8eac5be75c061afd39788675eb2e405`;
- raw coordinate SHA-256 `fa39271a98fefa2091483b7247d53e3744e1e26e478969310ce6f3560725c7f3`.

## Candidate selection

The existing TS07 artifact contains five Stage-A `CANDIDATE_FREATIC` records. They are not automatically positive Stage-B cases.

### Not selected: GMW000000004037 Tube 1

This is the strongest direct screen/fluctuation overlap case, but BRO reports both `tube_status` and `tube_in_use` as `onbekend`. The positive qualification workunit must not silently convert those unknown construction/use states into favourable evidence.

### Not selected: GMW000000020760 Tube 1

The tube is `gebruiksklaar` and in use, but the historic evidence bundle has an above-ground head fraction of about 0.0214 and the coordinate lies only about 7.0 m from its nearest REGIS x-boundary. It remains a useful later case but is not the cleanest first positive oracle.

### Not selected: GMW000000020764 Tube 1

Usable candidate, but its screen top is about 1.99 m below empirical q95 support. It would depend more strongly on additional hydrogeological interpretation than the selected case.

### Not selected: GMW000000020781 Tube 1

Usable direct series, but its coordinate is only about 4.0 m from the nearest REGIS x-boundary, creating an avoidable spatial-sensitivity complication for the first positive oracle.

### Selected: GMW000000020774 Tube 1

Direct/construction evidence from the immutable TS07 artifact:

- station: `GMW000000020774_T1`;
- GMW: `GMW000000020774`;
- GLD: `GLD000000007466`;
- BRO ground level: `9.85 m NAP`;
- RD coordinate: approximately `x=172274.997571`, `y=447781.978030`;
- tube status: `gebruiksklaar`;
- tube in use: `ja`;
- registered monitoring tubes at this GMW in the qualified bundle: exactly one;
- screen depth: `3.330–4.330 m-mv`;
- screen elevation: `6.520–5.520 m NAP`;
- series class: `fully_assessed`;
- observations: `31,704`;
- record span: `4,629 days`;
- empirical groundwater-depth q05/q50/q95: `1.498 / 1.812 / 2.054 m-mv`;
- above-ground fraction: `0.0`;
- screen top minus q95 depth: about `1.276 m` deeper than q95.

The selected case is deliberately not a trivial positive case: the screen is below the empirical fluctuation envelope. Positive admission therefore requires affirmative evidence that the screen is hydraulically connected to the free-surface regime. Stage-A `CANDIDATE_FREATIC` is not sufficient.

## Qualified coordinate mapping for the selected case

The existing qualified REGIS coordinate response was reused locally, with the already-qualified explicit-bound mapping semantics. No assumed cell-centre convention was used.

For `GMW000000020774`:

- x index: `1722`, bounds `[172200,172300]`, distances about `74.998 m` to west and `25.002 m` to east boundary;
- y index: `1477`, bounds `[447700,447800]`, distances about `81.978 m` to south and `18.022 m` to north boundary;
- nominal cell: `(1722,1477)`.

No universal near-boundary threshold is introduced. Because this is a positive-admission qualification case, unresolved regional spatial instability must fail closed. A bounded local sensitivity set is therefore permitted for this workunit without averaging:

1. nominal `(1722,1477)`;
2. east neighbour `(1723,1477)`;
3. north neighbour `(1722,1478)`;
4. north-east neighbour `(1723,1478)`.

These four alternatives are compared side by side and are never averaged.

## Current Stage-B evidence state

The following can already be established:

- direct observations: `AVAILABLE`;
- time-series usability: positive support from a long `fully_assessed` series;
- construction metadata: `AVAILABLE` for the required geometry/use fields in this case;
- same-GMW multi-filter evidence: `NOT_APPLICABLE` within the qualified bundle because exactly one monitoring tube is registered for this GMW;
- regional context: `UNKNOWN` pending bounded local-context qualification;
- hydraulic vertical-regime interpretation: not yet positively established;
- validation lineage: remains separate and is not decided by this workunit.

The existing `NO_DISTINCT_REGIME_EVIDENCE` enum must not be populated merely because no second monitoring tube exists. Absence of a second tube is not positive evidence of hydraulic continuity.

## Positive admission falsification conditions

This candidate must remain non-admitted if any of the following occurs:

1. required local construction or series evidence drifts or becomes unavailable;
2. bounded neighbouring regional columns produce materially inconsistent geometry/context relevant to the interval between the empirical fluctuation zone and the screen;
3. a separating interval is positively identified between the free-surface support and the monitoring screen;
4. hydrogeological continuity cannot be positively established with the available qualified evidence;
5. the only argument for admission is the historical 5 m heuristic or Stage-A `CANDIDATE_FREATIC` label;
6. missing or unknown evidence would need to be interpreted as favourable;
7. REGIS `freatisch` or lineage-coupled `kD` would be required as independent support.

## Exclusions

This workunit does not:

- expand to all GMWs;
- rerun broad BRO discovery;
- alter Stage-B evidence precedence;
- introduce a numeric adjudication score;
- introduce a universal screen-depth, head-difference or boundary-distance threshold;
- average REGIS neighbouring cells;
- infer hydraulic meaning from REGIS layer codes alone;
- enable production `allow_admissible=True`;
- decide LHM validation-lineage independence;
- recalibrate LHM or build WDM-conditioned corrections.

## Verdict

**DESIGN_POSITIVE_CASE_PENDING_LOCAL_CONTEXT**

The current evidence is insufficient to call `GMW000000020774_T1` `ADMISSIBLE_FREATIC`. It is, however, a bounded and scientifically suitable positive qualification candidate.

## Next permitted action

Acquire and parse only the four fixed REGIS v02r2s3 local-context columns listed above, using exactly `top`, `bottom`, `kh`, `kv`, and `c`, preserving raw hashes and missing `-9999 -> null` semantics. Then determine geometry/context stability around the interval from the empirical fluctuation zone to the screen.

If REGIS alone cannot positively establish hydraulic continuity without inventing unqualified layer semantics or thresholds, stop fail-closed and identify the minimum local higher-resolution evidence needed rather than deepening REGIS interpretation indefinitely.
