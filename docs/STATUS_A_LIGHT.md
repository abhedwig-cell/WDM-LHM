# Status A-light contract

## Purpose

WDM-LHM is research software for diagnosing differences between groundwater observations, WDM long-term groundwater-depth characteristics, and transient LHM/MODFLOW simulations. Status A-light is the repository contract used before any method is treated as scientifically admissible.

Status A-light deliberately separates four layers:

1. **Theory**: hydrological and statistical principles that are assumed to be valid.
2. **Conceptual model**: the entities, information flows, dependencies, and interpretation boundaries.
3. **Formal model**: equations, operators, estimands, sign conventions, and qualification rules.
4. **Implementation**: executable code, tests, input contracts, workflows, and evidence.

A code path is not admitted merely because it runs. It must be traceable to the three preceding layers and have qualification evidence appropriate to its scientific claim.

## Scientific invariants

- Direct groundwater observations are not interchangeable with WDM raster estimates or MODFLOW cell states.
- WDM is a statistical product, not a transient physical groundwater-flow model.
- WDM and LHM may share source information. WDM must not be treated as independent evidence unless lineage supports that claim.
- All WDM comparisons use groundwater depth relative to local ground level, positive downward, unless explicitly documented otherwise.
- Raw MODFLOW/LHM hydraulic heads may remain in m NAP, but conversion to depth must use an explicit ground-level source.
- A statistically corrected groundwater series is not automatically a physically consistent MODFLOW state. Fluxes, storage and other state variables remain tied to the original physical solution unless the physical model is rerun or consistency is demonstrated.
- Observation support must be explicit. A point observation, an interpolated WDM cell and a MODFLOW cell do not have identical spatial support.
- Missing lineage is represented as `unknown`, never silently as `no`.
- Held-out validation is required before claims of transferable improvement.

## Admission levels

| Level | Meaning |
| --- | --- |
| `EXPERIMENTAL` | Exploratory implementation; no scientific admission claim. |
| `QUALIFIED_SYNTHETIC` | Tests and synthetic cases demonstrate the intended numerical/statistical behaviour. |
| `QUALIFIED_REAL_DATA` | Real-data input passed admission gates and the method was evaluated on defined data. |
| `ADMITTED_BASELINE` | Method and evidence are sufficient for the stated baseline/reconstruction use. |
| `ADMITTED_SCENARIO` | Scenario-transfer and change-signal preservation have also been demonstrated. |

Current project level: **QUALIFIED_SYNTHETIC** for TS01–TS05. TS06 is additionally **technically live-qualified** for public BRO/PDOK ingestion through GitHub Actions, with 126,578 observations parsed from two fully assessed GLD series and zero ingest failures in the qualification smoke run. This does not promote the overall project to `QUALIFIED_REAL_DATA`: monitoring-tube suitability, lineage, LHM/MODFLOW pairing and TS05 admission still have to be demonstrated on the actual pilot dataset.

## Required repository evidence

Every admitted capability should identify:

- scientific purpose;
- theory/conceptual/formal references;
- exact input contract;
- code entry point;
- tests and test result;
- real-data dependencies and lineage;
- known exclusions;
- qualification verdict;
- next permitted action.

See `docs/architecture/TRACEABILITY.md`, `docs/qualification/TS01_TS06_CHECKPOINT.md`, and `docs/qualification/LIVE_BRO_QUALIFICATION.md`.
