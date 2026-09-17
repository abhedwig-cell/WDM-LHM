# Stage-B freatic adjudication — conceptual model

Status: design/qualification basis.

## 1. Entities

- **Monitoring tube**: one GMW tube with construction metadata and one or more GLD time series.
- **Freatic groundwater table**: the local upper free groundwater surface relevant to the stated WDM/LHM comparison use.
- **Empirical fluctuation zone**: robust observed range of groundwater depth derived from direct head observations and BRO ground level.
- **Vertical hydraulic structure**: evidence that hydraulic head depends materially on depth at the same location.
- **Construction record**: BRO ground level, filter interval, screen length, tube status and related metadata.
- **Regional hydrogeological context**: REGIS geometry and separately qualified hydraulic semantics at regional model support.
- **Evidence item**: one traceable observation, construction fact or contextual model-derived item with provenance and evidence state.
- **Hydraulic adjudication**: a fail-closed conclusion about freatic representativeness.
- **Validation-lineage gate**: a separate conclusion about independence for a stated validation use.

## 2. Evidence flow

```text
BRO GLD observations
  |--> empirical fluctuation zone
  |--> time-series quality
  |
  +----------------------------+
                               |
same-GMW multi-filter heads    |
  |--> vertical-head evidence  |
                               v
BRO construction metadata --> Stage-B local evidence record
                               |
REGIS regional context --------+
  | geometry + uncertainty     |
  | no local-truth promotion   |
                               v
                    hydraulic adjudication
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
     ADMISSIBLE_FREATIC  REVIEW/INSUFFICIENT  NOT_ADMISSIBLE
              |
              v
       separate lineage gate
              |
              v
     validation-use eligibility
```

## 3. Evidence hierarchy and override rule

The canonical order is:

1. direct observation evidence;
2. same-location multi-filter evidence;
3. local construction metadata;
4. regional hydrogeological context;
5. legacy heuristics.

Lower-priority evidence is supporting only. It cannot erase a contradiction in a higher-priority tier. A regional model can explain or contextualize direct evidence, but cannot turn a locally ambiguous or contradictory case into an automatic admission.

## 4. Direct-observation concepts

A tube can provide positive freatic support when its measured head variation and screen geometry are physically compatible with sampling the fluctuating free surface. The evidence record therefore preserves the empirical depth envelope and the full screen interval, not only one scalar depth.

Long-screen cases remain explicit because a screen may begin near the fluctuation zone yet extend into a deeper hydraulic domain.

## 5. Multi-filter concepts

Same-GMW filters are interpreted relationally. Persistent head separation demonstrates vertical hydraulic structure. It can establish that filters are not interchangeable and can make a shallower filter more plausible than a deeper one.

That relative statement is deliberately weaker than `ADMISSIBLE_FREATIC`.

## 6. REGIS concepts

REGIS contributes regional context, not local authority. Each evidence item retains:

- dataset/version;
- model support and cell index;
- selected column or sensitivity columns;
- unit geometry and provenance;
- missing values as missing;
- whether hydraulic semantics have actually been qualified.

For GMW000000004074, nominal and west-neighbour columns are distinct evidence alternatives. Their disagreement is itself an uncertainty signal and is never collapsed by averaging.

BRO ground level remains the authority for screen elevations. REGIS ground level is diagnostic only.

## 7. Evidence states

Every required field can be:

- `AVAILABLE`;
- `UNKNOWN`;
- `NOT_APPLICABLE`;
- `CONTRADICTORY`.

Interpretive propositions can additionally be labelled:

- `SUPPORTS_FREATIC`;
- `SUPPORTS_DISTINCT_DEEPER_REGIME`;
- `AMBIGUOUS`.

These labels are qualitative adjudication states, not numeric scores.

## 8. Output semantics

- **ADMISSIBLE_FREATIC**: positive direct local support is present, mandatory construction/time-series evidence is adequate, and no material unresolved higher-priority contradiction remains.
- **NOT_ADMISSIBLE_FREATIC**: robust positive local evidence supports a distinct/non-freatic hydraulic interpretation for the stated use.
- **REVIEW_REQUIRED**: enough evidence exists to expose a real scientific ambiguity, contradiction or spatial instability, but not to resolve it safely.
- **INSUFFICIENT_EVIDENCE**: required evidence is absent or unusable, so adjudication cannot proceed.

`REVIEW_REQUIRED` and `INSUFFICIENT_EVIDENCE` are different. The former preserves known ambiguity; the latter preserves missing knowledge.

## 9. Separate validation-lineage state

Hydraulic adjudication does not silently establish independent LHM validation. A separate lineage state is retained, for example:

- `VALIDATION_INDEPENDENCE_SUPPORTED`;
- `VALIDATION_INDEPENDENCE_UNKNOWN`;
- `VALIDATION_DEPENDENCE_PRESENT`.

`freatisch.img` and derived `kD` cannot supply independent corroboration against LHM in this workline.

## 10. Adversarial known cases

### GMW000000004104

Both filters are far below the observed near-surface fluctuation zone and same-location observations show persistent vertical head structure. Any rule that admits either filter as a normal freatic observation is falsified by the current evidence.

### GMW000000004074

Tube 1 is more plausible than Tube 2 as a freatic candidate, but its long screen extends below the observed fluctuation zone and its REGIS unit attribution is materially boundary-sensitive. The framework must preserve `more plausible` without converting it into automatic admission.
