# Formal model

## 1. Coordinate and sign convention

For station `i` and time `t`:

\[
d_i(t)=100\,[z_{mv,i}-h_i(t)]
\]

with `h` and `z_mv` in m NAP and `d` in cm below ground level. Increasing `d` means deeper groundwater.

## 2. Observation operator

Let `h_j(t)` be model head for model cell `j`. A station estimate is

\[
\hat h_i(t)=\sum_{j\in N_i} w_{ij}h_j(t), \qquad \sum_j w_{ij}=1.
\]

Nearest-cell uses one weight equal to one. IDW uses

\[
w_{ij}=\frac{r_{ij}^{-p}}{\sum_{k\in N_i}r_{ik}^{-p}}.
\]

The operator is rejected when configured distance or ground-level mismatch limits are exceeded.

## 3. GxG diagnostics

GHG and GLG are calculated from hydrological-year HG3/LG3 values using observations around the 14th and 28th of each month. GVG uses 14 March, 28 March and 14 April. The implementation reports actual valid years and does not infer 30-year representativeness from a shorter record.

## 4. Paired response model

For stress `R_t`:

\[
x_t(a)=a x_{t-1}(a)+R_t, \quad 0<a<1
\]

\[
d_t=c+g x_t(a)+\epsilon_t.
\]

The same model structure is fitted independently to observed and simulated groundwater depth. A characteristic response time is derived from the fitted persistence parameter.

## 5. Residual definition

\[
e_i(t)=d_{model,i}(t)-d_{obs,i}(t).
\]

Positive residual means the model groundwater is too deep relative to the observation.

## 6. Physical-regime diagnostics

Examples of binary or categorical regimes include:

- groundwater above/below an explicit drainage level;
- near-surface versus deeper-than-threshold groundwater;
- rising versus falling groundwater;
- season.

Differences are reported only when both sides of a regime satisfy a configured minimum sample count. Block bootstrap intervals preserve short-range temporal dependence better than iid resampling.

## 7. Incremental process diagnosis

A baseline predictive model for `e(t)` contains groundwater state terms and season. Candidate process variables, for example drainage, surface-water exchange or recharge, are then added at explicit lags.

The diagnostic quantity is out-of-sample improvement under blocked cross-validation:

\[
I_q = 100\frac{RMSE_{base}-RMSE_{base+q}}{RMSE_{base}}.
\]

A positive `I_q` is evidence of incremental predictive information, not proof that process `q` causes the residual.

## 8. Admission function

A real-data bundle is admitted only if mandatory schema, period, model-run identity, flux semantics, spatial support and held-out-design checks pass. Unknown lineage can be retained as a warning; absence of a held-out subset or unknown process-variable semantics are blockers for the associated scientific claims.

## 9. WDM conditioning boundary

No formal WDM-fusion equation is canonical yet. WDM conditioning remains outside admitted implementation until real-data diagnostics and lineage analysis establish what independent spatial information WDM contributes.
