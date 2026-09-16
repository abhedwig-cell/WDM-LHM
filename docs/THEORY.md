# Theory basis

## 1. Two different representations of the groundwater system

LHM/MODFLOW represents transient groundwater flow through a physical model with states, fluxes, storage terms and boundary conditions. WDM represents spatially distributed statistical characteristics of groundwater depth, especially GHG, GVG and GLG, estimated from groundwater observations and covariates.

The methods are therefore complementary, but they are not interchangeable.

## 2. Groundwater-depth convention

The comparison variable is groundwater depth below local ground level:

\[
d(t) = 100\,[z_{mv} - h(t)]
\]

where `h` and `z_mv` are in metres relative to the same vertical datum and `d` is in cm below ground level. Positive `d` means groundwater is below ground level.

## 3. Long-term groundwater characteristics

GHG and GLG summarize recurrent high and low groundwater-depth regimes using the Dutch GxG convention. GVG summarizes spring conditions. In this repository, GxG values computed from shorter periods are explicitly labelled with their available record length and are not automatically called 30-year climate-representative values.

## 4. Paired system identification

The principal diagnostic hypothesis is that the same statistical response model fitted separately to observed and simulated groundwater series can reveal differences that GxG alone cannot show, for example level, gain, memory and response time.

A first-order response state is used as the transparent baseline:

\[
x_t = a x_{t-1} + R_t
\]

\[
d_t = c + g x_t + \epsilon_t
\]

where `R` is a forcing such as precipitation minus evapotranspiration. The model is intentionally simple: its first purpose is comparative diagnosis, not replacement of groundwater physics.

## 5. State and process dependence

Groundwater errors can change across physical regimes. Drainage activation, approach to ground level, surface-water interaction, storage nonlinearity and hysteresis can all make a single additive correction implausible.

Therefore the residual

\[
e(t) = d_{model}(t) - d_{obs}(t)
\]

is analysed conditionally on groundwater depth, its temporal derivative, season, physical thresholds and modelled fluxes.

## 6. Dependence of evidence

If observations used to construct WDM were also used in LHM calibration, comparing or fusing WDM and LHM does not create two independent pieces of evidence. Shared elevation, soil, drainage and other covariates can create further dependence. This is why lineage and held-out validation are part of the scientific method rather than administrative metadata.

## 7. Uncertainty

Serial correlation in groundwater time series makes independent-sample uncertainty assumptions inappropriate. Block resampling and blocked cross-validation are therefore used in diagnostic workunits. WDM realizations can later represent WDM-internal spatial uncertainty, but they do not automatically represent common-mode uncertainty shared with LHM or source data.
