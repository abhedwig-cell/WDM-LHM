# Stage-B freatic admission — theory

Status: design basis, not yet an admitted automatic classifier.

## 1. Scientific question

Stage A answers whether a BRO monitoring tube is a plausible candidate for freatic use. Stage B asks a stronger question:

> Is there sufficient positive evidence that the measured head can represent the local freatic groundwater table for the stated WDM/LHM validation use?

This is an evidence-admission problem, not a generic classification problem.

## 2. Why screen depth alone is insufficient

A shallow screen can still measure a potentiometric head that differs from the local water table when vertical hydraulic gradients, semi-confining layers, perched systems, or the screen construction itself matter. Conversely, a historical fixed screen-depth threshold can reject a tube whose upper screen interval is close to the actual fluctuation zone.

Stage B therefore cannot be based on a single depth cutoff.

## 3. Direct observational evidence has priority

Same-location multi-filter measurements are especially informative because they directly expose vertical hydraulic structure. If two filters at the same GMW show a persistent head difference, the measurements cannot be treated as interchangeable samples of one scalar groundwater level.

Let a shallow and deep filter have synchronous heads h_s(t) and h_d(t):

\[
\Delta h_{sd}(t)=h_s(t)-h_d(t).
\]

Stage B preserves the distribution, sign persistence, overlap and correlation of \(\Delta h_{sd}\). No universal acceptable threshold is assumed in advance.

## 4. Screen placement versus empirical fluctuation zone

For local ground level z_mv and observed head h(t), groundwater depth is

\[
d(t)=z_{mv}-h(t).
\]

The empirical groundwater-fluctuation envelope is represented by robust quantiles of d(t). Screen top and bottom are compared with this envelope.

This comparison is evidence about measurement support, not proof by itself. A long screen extending far below the fluctuation zone can integrate deeper hydraulic conditions even when its upper edge is shallow.

## 5. Regional hydrogeological evidence

BRO REGIS II is a regional 3D hydrogeological model describing well-permeable and poorly permeable hydrogeological units and associated hydraulic properties on a 100 x 100 m grid. It is appropriate as supporting regional context for groundwater studies, but the provider explicitly warns that it is not sufficient by itself for local street- or building-scale interpretation.

Therefore REGIS evidence can support or contradict a local interpretation but cannot independently certify a monitoring tube as freatic.

Canonical public source checked 2026-09-16:

- https://www.pdok.nl/introductie/-/article/bro-regis-ii-hgm-
- https://www.bro-productomgeving.nl/bpo/latest/modellen/regis-ii-hydrogeologisch-model-hgm

Current documented model delivery at that date: REGIS II v2.2.3, BRO ID HGM000000000062.

## 6. Local geological evidence

Where REGIS is ambiguous or its regional scale is insufficient, higher-resolution or direct evidence is preferable. Candidate sources include GeoTOP and local borehole / lithological information. Missing local evidence must remain `unknown`; absence of data is not evidence for hydraulic openness.

## 7. Evidence hierarchy

Stage B uses the following conceptual priority:

1. direct local observations and construction metadata;
2. same-GMW multi-filter hydraulic evidence;
3. local borehole / high-resolution geological evidence;
4. regional hydrogeological context such as REGIS II;
5. generic historical heuristics.

Lower-priority evidence must not overrule strong contradictory higher-priority evidence without an explicit scientific disposition.

## 8. Fail-closed admission

Final automatic admission is not permitted when required evidence is missing, contradictory, or outside the qualified domain. The safe fallback is `REVIEW_REQUIRED`, not `ADMISSIBLE_FREATIC`.

## 9. Scale and scenario boundary

Freatic admission is a statement about observational representativeness at a monitoring location and specified period. It does not imply that the observation is independent of WDM or LHM calibration data, and it does not by itself establish suitability for scenario transfer.
