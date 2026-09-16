# Formal model for freatic monitoring-tube screening

Status: design model for issue #2. Thresholds marked `policy` are not physical constants.

## 1. Coordinates

For candidate tube `i`, let:

- `z_mv,i` = local ground-level elevation [m datum];
- `z_top,i` = screen-top elevation [m datum];
- `z_bot,i` = screen-bottom elevation [m datum], with `z_top >= z_bot`;
- `h_i(t)` = measured hydraulic head / groundwater level [m datum].

Screen depths below ground level are

\[
s_{top,i}=z_{mv,i}-z_{top,i}
\]

\[
s_{bot,i}=z_{mv,i}-z_{bot,i}.
\]

Observed groundwater/head depth is

\[
d_i(t)=z_{mv,i}-h_i(t).
\]

Positive depth means below ground level.

## 2. Mandatory geometry validation

A tube is structurally unresolved if any required elevation is missing or non-finite. Geometry is invalid if, beyond declared tolerances:

\[
z_{top,i} < z_{bot,i}
\]

or screen depth/order is internally inconsistent.

Invalid geometry blocks automatic admission and is reported separately from hydrological unsuitability.

## 3. Time-series support

For a selected assessment period define:

- `n_i`: number of valid measurements;
- `T_i`: elapsed record span;
- `q_p(d_i)`: robust empirical depth quantile;
- `A_i=q_{0.95}(d_i)-q_{0.05}(d_i)`: robust measured head-amplitude proxy.

Series requirements such as minimum `n_i`, minimum span and maximum gap are configurable **use-policy parameters**. They determine whether the intended analysis is possible; they do not determine freatic physics.

## 4. Geometric risk indicators

### 4.1 Historical-depth indicator

Historical groundwater-dynamics work used a criterion that a selected filter ended no deeper than 5 m below ground level. We retain

\[
R_{5m,i}=I(s_{bot,i}>5\,m)
\]

only as a provenance-labelled risk indicator `legacy_gd_depth_risk`.

`R_5m = 1` is **not** a standalone rejection rule.

### 4.2 Screen versus empirical head envelope

Define the deep observed head-depth quantile

\[
d_{deep,i}=q_{0.95}(d_i)
\]

and

\[
g_i=s_{top,i}-d_{deep,i}.
\]

A large positive `g_i` means the top of the filter lies below the depth reached by nearly all measured water levels. This increases the need for hydrogeological review, but cannot distinguish an open unconfined profile from a confined profile by itself.

## 5. Same-location vertical-head evidence

For two filters `a` and `b` at the same GMW location, align contemporaneous measurements on an explicitly documented temporal tolerance and calculate

\[
\Delta h_{ab}(t)=h_a(t)-h_b(t).
\]

Report at minimum:

\[
M_{ab}=\operatorname{median}(\Delta h_{ab})
\]

\[
S_{ab}=1.4826\,\operatorname{median}(|\Delta h_{ab}-M_{ab}|)
\]

plus overlap count, overlap span, sign fractions and correlation.

No universal numeric rejection threshold for `M_ab` is canonical yet. A threshold may only become canonical after measurement precision and hydrological significance are documented. Until then a persistent non-zero vertical separation is a review trigger and may become rejection evidence when interpreted with filter geometry/hydrogeology.

## 6. Two-stage decision system

### Stage A: BRO-only pre-screen

The pre-screen is allowed to use only reproducible BRO/GMW/GLD metadata and series evidence. It produces one of:

- `CANDIDATE_FREATIC`: data are structurally usable and no BRO-only risk indicator currently forces review;
- `REVIEW_DEEP_OR_AMBIGUOUS`: one or more risk indicators require further evidence;
- `INSUFFICIENT_DATA`: mandatory geometry/series information is missing;
- `NOT_USABLE_SERIES`: the GLD series fails the analysis-specific quality/period contract.

`CANDIDATE_FREATIC` means **candidate for further admission**, not physically proven freatic.

The historical 5 m criterion may be used as a transparent Stage-A routing rule because it is documented in the groundwater-dynamics methodology, but its use must be labelled `legacy_method_screen`, not `physical_freatic_test`.

### Stage B: scientific admission

Stage B incorporates vertical-head and hydrogeological evidence and yields:

- `ADMISSIBLE_FREATIC`;
- `REVIEW_REQUIRED`;
- `NOT_ADMISSIBLE_FREATIC`;
- `INSUFFICIENT_DATA`.

The conservative logic is:

1. invalid or missing mandatory evidence -> `INSUFFICIENT_DATA`;
2. demonstrated confined/deeper-head representation inconsistent with the target -> `NOT_ADMISSIBLE_FREATIC`;
3. positive unconfined/freatic evidence with no material contradiction -> `ADMISSIBLE_FREATIC`;
4. otherwise -> `REVIEW_REQUIRED`.

Thus uncertainty is not converted to automatic acceptance.

## 7. Evidence record

Every verdict must retain machine-readable evidence, including at least:

```text
station_id
gmw_bro_id
tube_number
gld_bro_id
screen_top_depth_m
screen_bottom_depth_m
n_observations
record_span_days
q05_depth_m
q50_depth_m
q95_depth_m
legacy_gd_depth_risk
screen_below_empirical_envelope_m
tube_status
tube_in_use
series_class
peer_filter_count
vertical_head_evidence_status
hydrogeology_evidence_status
prescreen_verdict
admission_verdict
reason_codes
```

`null` remains `null`; missing evidence is never converted to zero, false or favourable status.

## 8. Separation from final paired analysis

A final validation tube must pass all relevant gates:

\[
A_{final}=A_{series}\cap A_{freatic}\cap A_{support}\cap A_{lineage/design}.
\]

Where:

- `A_series`: measurement-period/quality admission;
- `A_freatic`: this screening capability;
- `A_support`: spatial observation-operator admission;
- `A_lineage/design`: held-out and information-dependence requirements.

Passing the freatic gate alone does not admit a station to model validation.
