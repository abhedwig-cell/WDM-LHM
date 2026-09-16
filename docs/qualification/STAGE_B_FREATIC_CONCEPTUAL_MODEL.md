# Stage-B freatic admission — conceptual model

Status: design basis.

## Entities

- **Monitoring tube**: one GMW tube with screen interval and GLD time series.
- **Freatic groundwater table**: the upper free groundwater surface relevant to WDM groundwater-depth characteristics.
- **Vertical hydraulic structure**: differences in head between depths at the same location.
- **Empirical fluctuation envelope**: robust range of observed groundwater depth at the candidate tube.
- **Hydrogeological unit**: permeable or poorly permeable unit from regional/local geological evidence.
- **Evidence item**: one traceable observation, model-derived context item, or construction fact with provenance.
- **Admission decision**: a fail-closed interpretation of the evidence for one stated use.

## Evidence flow

```text
BRO GMW/GLD metadata + observations
        |
        +--> Stage-A candidate routing
        |
        +--> empirical fluctuation envelope
        |
        +--> same-GMW multi-filter diagnostics

REGIS II / GeoTOP / borehole evidence
        |
        +--> hydrogeological context

all evidence + provenance
        |
        v
Stage-B evidence record
        |
        v
ADMISSIBLE_FREATIC / REVIEW_REQUIRED / NOT_ADMISSIBLE_FREATIC
```

## Key design principle

Evidence ingestion and scientific admission are separate components. A new external dataset may enrich the evidence record without changing admission semantics. Conversely, an admission-rule change is a separate scientific decision surface and requires explicit qualification.

## Positive evidence examples

- screen geometry consistent with the measured fluctuation zone;
- a shallow filter behaves distinctly from a deeper filter in a way consistent with vertical hydraulic structure;
- no mapped regional confining unit separates the shallow screen from the near-surface groundwater system, while the model scale is appropriate enough to be informative;
- local geological/borehole evidence supports hydraulic connection.

## Contradictory evidence examples

- strong persistent same-location vertical head difference showing the candidate belongs to a different hydraulic regime than a shallower filter;
- screen entirely far below the empirical fluctuation zone;
- a mapped poorly permeable unit separates the screen from the near-surface system;
- artesian or physically implausible head behaviour for a freatic interpretation.

## Unknown evidence

Unknown evidence is first-class state. It is not converted to favourable evidence and does not receive a default score of zero.

## REGIS role

REGIS II is supporting regional context. It can identify the modeled presence and geometry of permeable and poorly permeable units around a candidate location, but its 100 m support and model uncertainty prevent treating a single extracted column as exact local truth.

## Admission boundary

Stage B may eventually automate admission only for cases inside a qualified evidence domain. Ambiguous cases remain review cases even if a statistical classifier could assign them a high probability.
