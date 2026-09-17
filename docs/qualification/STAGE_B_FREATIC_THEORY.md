# Stage-B freatic adjudication — theory

Status: design/qualification basis. No production classifier is admitted by this document.

## 1. Scientific question

Stage A asks whether a BRO monitoring tube is worth further review. Stage B asks a stronger, use-specific question:

> Is there sufficient positive local evidence that the observed head represents the local freatic groundwater table, without unresolved evidence that it instead represents a deeper or otherwise distinct hydraulic regime?

This is an evidence-adjudication problem, not a generic classification or scoring problem.

For WDM/LHM validation there is a second, separate question: whether an otherwise freatically representative observation is sufficiently independent of the model lineage for the stated validation use. Hydraulic representativeness and validation independence must not be collapsed into one inference.

## 2. Why depth rules are not physical admission rules

A shallow screen can still measure a potentiometric head that differs from the local water table when vertical gradients, semi-confining units, perched systems or screen construction matter. Conversely, a fixed historical depth threshold can reject a tube whose upper screen interval lies close to the observed groundwater-fluctuation zone.

The historical 5 m rule therefore remains a routing/review heuristic only. It is never positive proof of freatic representativeness and never an automatic disqualifier.

## 3. Evidence precedence

Stage B uses the following precedence. Higher tiers constrain the interpretation of lower tiers.

1. **Direct observation evidence**
   - empirical groundwater-fluctuation zone;
   - screen position relative to that zone;
   - time-series quality and support.
2. **Same-location multi-filter evidence**
   - persistent head difference;
   - sign persistence;
   - temporal coherence;
   - evidence for vertical hydraulic structure.
3. **Local construction metadata**
   - BRO filter top/bottom and screen length;
   - BRO ground level used to derive screen elevation;
   - tube status and construction metadata where available.
4. **Regional hydrogeological context**
   - qualified REGIS geometry and, only after separate semantic qualification, regional `kh`, `kv` and `c`;
   - explicit support-scale and spatial-sensitivity warnings.
5. **Legacy heuristics**
   - historical criteria such as the 5 m rule;
   - routing/review signal only.

A lower tier cannot override materially contradictory higher-tier evidence merely because it is more complete or easier to automate.

## 4. Direct observations have local precedence

For local BRO ground level z_mv and observed head h(t), groundwater depth is

\[
d(t)=z_{mv}-h(t).
\]

Robust empirical quantiles of d(t) describe the observed fluctuation zone. Screen top and bottom are compared with that zone.

This comparison is evidence, not a universal threshold test. A long screen whose upper edge approaches the fluctuation zone but whose lower part extends well below it can mix or integrate deeper hydraulic conditions. Such geometry is intrinsically more ambiguous than a short screen tightly supporting the fluctuating free surface.

## 5. Same-location multi-filter evidence

For shallow and deep filters at one GMW,

\[
\Delta h_{sd}(t)=h_s(t)-h_d(t).
\]

The adjudication preserves at least overlap count/span, median difference, robust scale, sign persistence and temporal correlation. A persistent difference is direct evidence that the filters are not interchangeable samples of one hydraulic head.

No universal acceptable value of \(\Delta h\), gradient, sign fraction or correlation is assumed. Interpretation is relational: a shallow tube may become more plausible than a deeper tube without thereby becoming sufficiently proven as a clean freatic observation.

## 6. REGIS is supporting regional context

REGIS v02r2s3 is a regional 100 x 100 m hydrogeological model. In this workline its qualified contribution is restricted to unit geometry and, after separate semantic qualification, supporting regional hydraulic properties.

It is not local truth. The current real-data qualification demonstrates why:

- GMW000000004074 lies only about 5.6 mm east of a REGIS cell boundary and its shallow screen changes materially in unit attribution between the nominal and west-neighbour columns;
- GMW000000004104 shows about +1.34 m REGIS-versus-BRO ground-level mismatch.

The two 4074 columns must therefore remain side-by-side sensitivity evidence and must never be silently averaged.

`freatisch` / `freatisch.img` is excluded as independent evidence against LHM because its production lineage is substantially LHM-derived. `kD` is likewise excluded as independent Stage-B evidence here because its saturated thickness depends on that freatic surface.

## 7. Positive evidence is required for admission

`ADMISSIBLE_FREATIC` cannot be reached from absence of contradiction alone. It requires positive local evidence that the tube supports the fluctuating free surface, together with sufficient time-series quality and construction metadata, and no unresolved higher-priority evidence for a distinct hydraulic regime.

Regional-model agreement may strengthen confidence but cannot create admission when the required direct local support is absent.

## 8. Fail-closed ambiguity

The adjudication distinguishes:

- `ADMISSIBLE_FREATIC`: positive local support and no material unresolved contradiction;
- `NOT_ADMISSIBLE_FREATIC`: robust positive evidence that the tube represents a non-freatic or distinct hydraulic regime for the stated use;
- `REVIEW_REQUIRED`: evidence exists but is contradictory, spatially unstable, scale-sensitive or otherwise scientifically ambiguous;
- `INSUFFICIENT_EVIDENCE`: mandatory evidence needed to adjudicate is missing or unusable.

Unknown is never converted to no, and missing is never converted to zero, a default, or favourable evidence.

## 9. Validation independence is a separate gate

A physical `ADMISSIBLE_FREATIC` conclusion does not by itself establish independent validation eligibility. For LHM validation, lineage must be assessed separately. Model-derived surfaces or quantities whose construction depends on LHM cannot be reused as apparently independent corroboration.

## 10. Falsification principle

The framework is unacceptable if it:

- admits either 4104 filter as a normal freatic observation despite their deep screens and persistent vertical structure;
- converts 4074 Tube 1 into a certain freatic observation merely because it is shallower than Tube 2;
- resolves the 4074 REGIS boundary sensitivity by averaging the neighbouring columns;
- allows a REGIS layer code or regional hydraulic property to overrule contradictory direct local observations;
- turns missing or unknown evidence into favourable evidence.
