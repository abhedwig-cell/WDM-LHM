# Data lineage and provenance

## Mandatory station lineage

Each station used in real-data work should carry at least:

- `station_id`
- BRO/GMW identity and tube number where applicable
- location and coordinate reference system
- ground-level value and source
- screen/filter geometry
- `used_in_wdm = yes | no | unknown`
- `used_in_lhm_calibration = yes | no | unknown`
- `heldout_group = train | development | heldout | unknown`
- metadata source and retrieval date

`unknown` is a valid state and must not be rewritten to `no` without evidence.

## Model-run provenance

A model time series should be tied to a run record containing model family/version, run ID, period, relevant input configuration and extraction procedure. Re-running or replacing model outputs without updating the run identity invalidates previous evidence that depended on the old run.

## Flux semantics

Every process variable must define:

- variable name;
- unit;
- positive sign convention;
- represented physical process;
- source package/budget term;
- temporal support (instantaneous, daily mean, daily total, etc.).

No process-diagnosis claim is admitted when the variable semantics are unknown.

## BRO/PDOK provenance

TS06 caches raw bytes by URL, preserves source identifiers and writes a manifest. BRO/PDOK data are primary public sources for the ingest route, but BRO completeness is not assumed to be identical to historical DINO completeness.

## WDM provenance

Before WDM enters any comparison or conditioning step, record:

- WDM version/release;
- reference period where known;
- data sources and covariates relevant to the study area;
- overlap with selected monitoring wells;
- overlap with LHM calibration/support data;
- realization/uncertainty product used.
