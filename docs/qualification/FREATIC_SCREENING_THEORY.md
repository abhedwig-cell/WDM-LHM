# Theory basis for freatic monitoring-tube screening

Status: design basis for issue #2. Not yet an admitted screening algorithm.

## 1. Target quantity

The target for WDM/LHM comparison is the **freatic groundwater table**, expressed as groundwater depth below local ground level. A BRO GLD series records groundwater level and/or hydraulic head at the monitoring filter. Those quantities are not automatically interchangeable.

A monitoring tube can therefore be technically valid and fully assessed while still being unsuitable as evidence for the local freatic water table.

## 2. Why filter position matters

In an open, unconfined profile a filter intended to observe the freatic groundwater table should be hydraulically connected to the shallow groundwater system. Wageningen research on measurement and interpretation distinguishes a shallow filter in the groundwater-table fluctuation zone from a deeper filter used to observe hydraulic head. In profiles with stagnating layers, perched water tables and vertical head differences may require additional shallow filters.

Consequently, absolute screen depth alone is not a physical definition of freatic suitability. Historical groundwater-dynamics work has used practical depth criteria, including a screen ending no deeper than 5 m below ground level, but such criteria are treated here only as risk indicators unless supported by hydrogeological evidence.

## 3. Evidence hierarchy

Freatic suitability is inferred from several evidence layers:

1. **Construction and metadata**: ground level, screen top/bottom, tube status, measurement quality and period.
2. **Time-series behaviour**: observed head range, continuity, plausibility relative to ground level and temporal dynamics.
3. **Vertical-head evidence**: contemporaneous series from multiple filters in the same or immediately adjacent well can reveal systematic vertical gradients.
4. **Hydrogeological context**: aquitards, stagnating layers, confined/semi-confined conditions, perched systems and local groundwater-flow setting.
5. **Observation support**: representativeness of the local point measurement for the MODFLOW/LHM cell and for WDM comparison.
6. **Lineage**: use of the tube in WDM construction and/or LHM calibration.

No single weak indicator should dominate stronger contradictory evidence.

## 4. Interpretation classes

The screening must distinguish at least three outcomes:

- `ADMISSIBLE_FREATIC`: available evidence supports use as a freatic observation for the stated analysis.
- `REVIEW_REQUIRED`: evidence is incomplete, ambiguous or internally conflicting. The tube must not silently enter the admitted validation set.
- `NOT_ADMISSIBLE_FREATIC`: evidence demonstrates that the series represents a deeper/confined hydraulic head or otherwise fails the freatic observation contract.

A fourth technical outcome, `INSUFFICIENT_DATA`, is useful when mandatory metadata or time-series support is missing. It is not equivalent to `NOT_ADMISSIBLE_FREATIC`.

## 5. Conservative decision principle

Absence of evidence for confinement is not evidence of an unconfined freatic connection. Conversely, a deep screen is not by itself proof of non-freatic behaviour in a hydraulically open homogeneous profile.

Therefore ambiguous cases resolve to `REVIEW_REQUIRED` or `INSUFFICIENT_DATA`, not to an optimistic automatic admission.

## 6. Vertical gradients

If multiple filters at the same location show persistent, reproducible head differences, this is direct evidence that hydraulic head varies with depth. A deeper filter must then not be treated as interchangeable with the freatic water table without additional evidence.

The magnitude, persistence and uncertainty of a vertical-head difference must be reported explicitly. A future automated threshold may only be introduced after measurement precision and practical hydrological significance have been documented.

## 7. Time-series quality versus hydrological meaning

BRO assessment status describes the quality status of registered measurements. It does not classify a filter as freatic. Fully assessed GLD data are preferred for quantitative work, but measurement quality and hydrological representativeness remain separate admission dimensions.

## 8. Source basis

Primary sources used for this design:

- BRO Product Environment, Grondwaterstandonderzoek (GLD): https://www.bro-productomgeving.nl/bpo/latest/grondwatermonitoring/grondwaterstandonderzoek-gld
- BRO/PDOK GM monitoring-tube characteristics: https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/ogc/v1/collections/gm_gmw_monitoringtube/items?f=html
- De Gruijter et al. (2004), *Grondwater opnieuw op de kaart*, Alterra report 915: https://edepot.wur.nl/26169
- Ritzema et al. (2012), *Meten en interpreteren van grondwaterstanden*: https://edepot.wur.nl/215081

The 5 m screen criterion in De Gruijter et al. is retained as historical methodological context, not promoted to a universal physical rule.
