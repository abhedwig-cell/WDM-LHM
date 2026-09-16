# Conceptual model

## Entities

- **Groundwater monitoring well / tube**: local observation support with location, filter geometry, ground level and time series.
- **LHM/MODFLOW model cell**: spatial model support with transient head and optional water-balance/process terms.
- **WDM cell**: statistical spatial prediction of long-term groundwater-depth characteristics and associated uncertainty.
- **Meteorological forcing**: precipitation, potential evapotranspiration or derived recharge/stress series.
- **Observation operator**: explicit mapping from model support to monitoring support.
- **Lineage record**: states whether a monitoring series or related information contributed to WDM or LHM calibration and whether it is held out.

## Information flow

```text
BRO GMW/GLD observations ───────────────┐
                                        ├─> admission + observation operator
LHM/MODFLOW heads + fluxes ─────────────┘            │
                                                     v
                                           paired diagnostics
                                                     │
                         ┌───────────────────────────┼───────────────────────────┐
                         v                           v                           v
                    GxG benchmark            response comparison         regime/process residuals
                         │                           │                           │
                         └───────────────────────────┴───────────────────────────┘
                                                     │
                                                     v
                                               held-out evidence
                                                     │
                              WDM spatial information enters only after lineage audit
```

## Interpretation hierarchy

1. At a reliable monitoring location, direct observations are the primary evidence for transient groundwater behaviour.
2. LHM/MODFLOW supplies physically coherent transient dynamics and water-balance context.
3. WDM supplies long-term spatial information and uncertainty, especially between monitoring locations.
4. Statistical post-processing is a derived product unless physical consistency is restored through the physical model.

## Observation support

A monitoring tube does not represent an arbitrary nearby MODFLOW cell by default. The observation operator records method, distance, weights and ground-level mismatch. Current transparent baselines are nearest-cell and inverse-distance weighting. More physically informed operators may be added only with separate qualification.

## Research sequence

- TS01: paired single-station time-series diagnostics.
- TS02: multiwell observation operator and batch diagnostics.
- TS03: state/regime-dependent residual diagnosis.
- TS04: incremental process-flux diagnosis with lags.
- TS05: real-data admission and lineage gate.
- TS06: BRO/PDOK ingestion.

The next scientific phase is real-data qualification, not automatic construction of a correction or WDM fusion layer.
