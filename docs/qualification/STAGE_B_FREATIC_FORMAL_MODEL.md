# Stage-B freatic adjudication — formal decision model

Status: design/qualification basis. No numeric score and no production automatic admission rule are canonical yet.

## 1. Candidate record

For tube i define:

- BRO ground level: \(z_{mv,i}\) [m NAP];
- screen top/bottom: \(z_{top,i}, z_{bot,i}\) [m NAP];
- observed head series: \(h_i(t)\) [m NAP];
- tube/construction status metadata: \(C_i\).

Groundwater depth is

\[
d_i(t)=z_{mv,i}-h_i(t).
\]

Let the empirical fluctuation summary be

\[
Q_i=(q_{05,i},q_{50,i},q_{95,i}).
\]

Screen depths below ground are

\[
s_{top,i}=z_{mv,i}-z_{top,i},\qquad s_{bot,i}=z_{mv,i}-z_{bot,i}.
\]

The full interval \([s_{top,i},s_{bot,i}]\) is retained. No single screen-depth scalar replaces it.

## 2. Direct-observation evidence

Define a direct-observation record

\[
D_i=(Q_i,S_i,T_i)
\]

where \(S_i\) is the screen-versus-fluctuation geometric relation and \(T_i\) is time-series quality/support.

`S_i` is descriptive. It may distinguish cases such as:

- screen materially supporting the observed fluctuation zone;
- long screen spanning the fluctuation zone and deeper intervals;
- screen entirely below the observed fluctuation zone;
- unknown because required geometry is unavailable.

No universal numeric boundary between these categories is admitted in this workunit.

## 3. Same-location multi-filter evidence

For shallow/deep pair \((s,d)\):

\[
\Delta h_{sd}(t)=h_s(t)-h_d(t).
\]

The evidence record contains at least:

- \(n_{overlap}\);
- overlap span;
- median \(\Delta h\);
- robust scale of \(\Delta h\);
- \(P(\Delta h>0)\);
- \(P(\Delta h<0)\);
- correlation \(corr(h_s,h_d)\).

These statistics establish the character and persistence of vertical structure but do not receive universal decision weights or thresholds.

## 4. Construction evidence

The construction record must retain:

\[
C_i=(z_{mv,i},z_{top,i},z_{bot,i},L_i,status_i,provenance_i)
\]

where \(L_i\) is screen length. BRO ground level is authoritative for conversion between depth below ground and elevation. REGIS ground level may only be diagnostic.

Missing construction fields remain `UNKNOWN`.

## 5. Regional hydrogeological context

For each qualified REGIS column c, define

\[
R_{i,c}=\{(u_k,z_{top,k},z_{bot,k},p_k)\}_{k=1}^{K}
\]

where \(u_k\) is layer identity and \(p_k\) contains provenance and any separately qualified hydraulic semantics.

For spatially sensitive locations, the record is a set of alternatives

\[
R_i=\{R_{i,c_1},R_{i,c_2},...\}
\]

not an average column.

For GMW000000004074 specifically, nominal cell `(1703,1407)` and west sensitivity cell `(1702,1407)` are preserved independently because the monitoring coordinate lies about 0.0056 m east of their shared boundary.

`freatisch` and `kD` are excluded from independent Stage-B validation evidence under the current lineage disposition.

## 6. Evidence-state algebra

For required evidence field e:

\[
state(e)\in\{AVAILABLE,UNKNOWN,NOT\_APPLICABLE,CONTRADICTORY\}.
\]

No transformation is permitted in which

\[
UNKNOWN\rightarrow 0,
\]

or

\[
UNKNOWN\rightarrow FAVOURABLE.
\]

## 7. Hydraulic adjudication outputs

\[
A_i\in\{ADMISSIBLE\_FREATIC,NOT\_ADMISSIBLE\_FREATIC,REVIEW\_REQUIRED,INSUFFICIENT\_EVIDENCE\}.
\]

### 7.1 Mandatory conditions for `ADMISSIBLE_FREATIC`

Automatic admission is permitted only if all of the following are positively established within the qualified domain:

1. usable direct head observations define an empirical fluctuation zone;
2. screen geometry provides positive support for sampling the fluctuating free surface, rather than merely lacking a known contradiction;
3. time-series quality is adequate for the stated comparison period/use;
4. required construction metadata are available and internally consistent;
5. same-GMW multi-filter evidence, when available, does not provide unresolved higher-priority evidence that the candidate belongs to a distinct hydraulic regime;
6. any regional hydrogeological evidence used is supporting only and does not contain unresolved spatial instability material to the interpretation;
7. no required field is `UNKNOWN` where that field is necessary to establish conditions 1–6.

Condition 2 is deliberately positive: `no evidence against` is insufficient.

At the present design checkpoint, production automation of this state remains disabled until these qualitative conditions are implemented and independently qualified.

### 7.2 `NOT_ADMISSIBLE_FREATIC`

This state requires robust positive local evidence for a distinct/non-freatic interpretation, for example a screen clearly outside the observed free-surface support combined with persistent same-location vertical structure. It must not be produced merely because regional context is missing or one heuristic threshold is exceeded.

### 7.3 `REVIEW_REQUIRED`

Use when evidence is substantive but scientifically ambiguous, contradictory, spatially unstable or scale-sensitive. A known boundary-sensitivity conflict is `REVIEW_REQUIRED`, not `INSUFFICIENT_EVIDENCE` and not an invitation to average the alternatives.

### 7.4 `INSUFFICIENT_EVIDENCE`

Use when mandatory evidence needed for adjudication is absent or unusable. Missing information is not negative evidence.

## 8. Evidence precedence operator

Let evidence tiers be \(E_1...E_5\) in descending priority. For material contradiction between tiers,

\[
E_j \not\succ E_i\quad\text{for}\quad j>i,
\]

meaning lower-priority evidence cannot overrule higher-priority evidence without an explicit scientific disposition.

Therefore REGIS context cannot independently transform a direct-observation `REVIEW_REQUIRED` case into `ADMISSIBLE_FREATIC`.

## 9. Separate validation-lineage gate

Define

\[
L_i\in\{VALIDATION\_INDEPENDENCE\_SUPPORTED,VALIDATION\_INDEPENDENCE\_UNKNOWN,VALIDATION\_DEPENDENCE\_PRESENT\}.
\]

Hydraulic admission and validation eligibility are distinct:

\[
VALIDATION\_USABLE_i \Rightarrow (A_i=ADMISSIBLE\_FREATIC)\land(L_i=VALIDATION\_INDEPENDENCE\_SUPPORTED).
\]

The converse is not assumed automatically because additional use-specific quality requirements may apply.

## 10. Qualification/falsification cases

### GMW000000004104 Tube 1 and Tube 2

Expected safety property:

\[
A_i\neq ADMISSIBLE\_FREATIC.
\]

The current evidence supports `NOT_ADMISSIBLE_FREATIC`: both screens are far below the observed near-surface fluctuation zone, while the same-location pair shows persistent vertical head structure. This case-specific conclusion does not introduce a universal depth threshold.

### GMW000000004074 Tube 1

Expected state under current evidence:

\[
A_i=REVIEW\_REQUIRED.
\]

Reasons: the upper screen is close to the observed fluctuation zone, the full screen extends materially deeper, persistent Tube1–Tube2 head separation demonstrates vertical structure, and REGIS unit attribution is materially unstable across a cell boundary only millimetres from the monitoring coordinate.

### GMW000000004074 Tube 2

Expected safety property:

\[
A_i\neq ADMISSIBLE\_FREATIC.
\]

The deep screen plus persistent separation from the shallower filter is positive evidence for a distinct deeper hydraulic regime. Under the current case record the intended adjudication is `NOT_ADMISSIBLE_FREATIC`.

## 11. Forbidden shortcuts

The formal operator must never:

- use the historical 5 m criterion as a physical admission rule;
- invent a universal vertical-head-difference threshold;
- average the two 4074 REGIS columns;
- infer hydraulic semantics from a layer code before those semantics are qualified;
- use REGIS `freatisch` or lineage-coupled `kD` as independent evidence against LHM;
- replace BRO ground level with REGIS ground level for screen elevation;
- impute missing evidence as zero, default, average or representative value.
