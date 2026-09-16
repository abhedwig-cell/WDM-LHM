# Stage-B freatic admission — formal model

Status: design basis; no automatic admission rule is canonical yet.

## 1. Candidate

For tube i:

- local ground level: z_mv,i [m NAP]
- screen top: z_top,i [m NAP]
- screen bottom: z_bot,i [m NAP]
- observed head series: h_i(t) [m NAP]

Depths below ground level are

\[
s_{top,i}=z_{mv,i}-z_{top,i}, \qquad s_{bot,i}=z_{mv,i}-z_{bot,i}.
\]

Observed groundwater depth is

\[
d_i(t)=z_{mv,i}-h_i(t).
\]

## 2. Empirical fluctuation evidence

Let

\[
Q_i=(q_{05,i},q_{50,i},q_{95,i})
\]

be robust empirical quantiles of d_i(t).

Useful descriptive distances include

\[
\delta_{top,i}=s_{top,i}-q_{95,i}
\]

and

\[
\delta_{bot,i}=s_{bot,i}-q_{95,i}.
\]

These are evidence variables, not admission thresholds.

## 3. Same-location vertical-head evidence

For a shallow/deep tube pair (s,d) belonging to the same GMW:

\[
\Delta h_{sd}(t)=h_s(t)-h_d(t).
\]

The evidence record contains at least:

- n_overlap;
- overlap span;
- median(Delta h);
- robust scale of Delta h;
- P(Delta h > 0);
- P(Delta h < 0);
- correlation(h_s,h_d).

No universal decision threshold on any one statistic is canonical in this workunit.

## 4. Hydrogeological column evidence

For external hydrogeological model M at horizontal support cell c(i), define a vertical ordered set

\[
H_i^M=\{(u_k,z_{top,k},z_{bot,k},T_k,P_k)\}_{k=1}^K
\]

where:

- u_k = hydrogeological unit identity;
- z_top,k, z_bot,k = modeled geometry;
- T_k = unit type / hydraulic role where available (for example permeable versus poorly permeable);
- P_k = provenance and model-version metadata.

Derived evidence may describe whether one or more modeled poorly permeable units occur between the near-surface fluctuation zone and the screen interval.

Crucially:

\[
\text{no mapped confining unit} \not\Rightarrow \text{proved local hydraulic connection}.
\]

## 5. Evidence state

Every evidence field has state in

\[
\{AVAILABLE, UNKNOWN, NOT_APPLICABLE, CONTRADICTORY\}.
\]

`UNKNOWN` is never numerically imputed as favourable.

## 6. Admission outputs

The only permitted Stage-B outputs are:

- `ADMISSIBLE_FREATIC`
- `REVIEW_REQUIRED`
- `NOT_ADMISSIBLE_FREATIC`

At this stage, automatic production of `ADMISSIBLE_FREATIC` is disabled until a rule has been separately proposed and qualified.

The canonical interim operator therefore is:

\[
A(E_i)=REVIEW\_REQUIRED
\]

unless explicit disqualifying evidence supports `NOT_ADMISSIBLE_FREATIC` under an already qualified rule.

## 7. Separation of concerns

The following are distinct contracts:

1. acquisition of external model evidence;
2. extraction of hydrogeological column evidence;
3. construction of the evidence record;
4. scientific admission logic.

Changing one contract does not silently alter the others.

## 8. Regional-model limitation

REGIS II extraction occurs on model support of approximately 100 x 100 m. Point coordinates of a monitoring tube select a regional model column but do not change that support to point scale. The evidence record must retain model cell/support and model version.
