# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **QUALIFIED_GEOTOP_METADATA_GATE_1**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12. It acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition and interpretation remain separate.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start and Gate-1 qualification: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- qualified Gate-1 head: `099ea43a845179df70d811c7826a1a9badad355c`
- parent verdict: `QUALIFIED_LOCAL_BHRG_ACQUISITION_NO_LOCAL_OBJECTS`
- tracking surface: issue #4
- pull request: #13

## Reused immutable target evidence

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m`
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW, BRO, REGIS or GeoTOP rediscovery is permitted in this workunit.

## GeoTOP authority and scale boundary

The bounded public source is the TNO/DINOloket GeoTOP OPeNDAP dataset:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc`

GeoTOP is supporting subregional geological context, not local well truth. No GeoTOP result may override direct groundwater observations, same-location multi-filter evidence or BRO construction metadata.

## Gate 1: qualified metadata boundary

Gate 1 retrieved only DAP2 `.dds` and `.das` metadata. It did not request coordinate values, voxel values or any model class values.

### Live qualification

Exact qualified head:

`099ea43a845179df70d811c7826a1a9badad355c`

Ordinary CI:

- run `35188889824`: **PASS**;
- Python 3.10: `93 passed`;
- Python 3.12: `93 passed`.

Live metadata workflow:

- run `35188889782`: **PASS**;
- artifact ID: `10483405874`;
- artifact name: `stage-b-geotop-20774-metadata-35188889782`;
- artifact ZIP SHA-256: `5cca45335d6e041cb852d28f0d5f126931584cbca3e522b1066198d3b4b9c62f`;
- DDS SHA-256: `845bf38ef3bcbed025e0a01925508f5f143644c188e9ff703651a85d8fe5ba07`;
- DAS SHA-256: `50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc`.

### Live dataset contract

Declared dimensions:

- `x = 2646`;
- `y = 2811`;
- `z = 313`.

Confirmed declared variables include:

- `x`;
- `y`;
- `z`;
- `strat`;
- `lithok`.

The live workflow explicitly verified:

- `metadata_only = true`;
- `data_requests_issued = false`;
- `constraint_expression_issued = false`;
- `voxel_values_read = false`;
- `lithology_interpretation_performed = false`;
- `hydraulic_interpretation_performed = false`;
- `screen_correlation_performed = false`;
- `admission_decision_performed = false`;
- `allow_admissible_enabled = false`.

## Parser reconciliation during Gate 1

Three live-service syntax differences were encountered and corrected without changing scientific assumptions:

1. the DAP2 dataset envelope uses a dataset name that must be parsed generically rather than hard-coded to `geotop`;
2. DAP2 Grid structures may repeat coordinate declarations; byte-for-byte semantic duplicates are deduplicated, while conflicting duplicates still fail closed;
3. DAS attribute-section indentation is not fixed to exactly two spaces; one-or-more whitespace is accepted while an actual nested section remains required.

These are protocol/parser contract corrections only. Dataset identity, endpoint constraints, required coordinate semantics and the no-data/no-interpretation boundary were not relaxed.

## Gate-1 verdict

**QUALIFIED_GEOTOP_METADATA_BOUNDARY**

The dataset identity, dimensions and required variable inventory are now pinned sufficiently to design the next bounded acquisition gate. This verdict does not qualify any GeoTOP geological interpretation and does not change the Stage-B adjudication state of `GMW000000020774_T1`.

## Gate 2: coordinate-axis mapping only

Gate 2 may now acquire only the coordinate axes `x`, `y` and `z` from the same fixed dataset. It must remain separate from categorical voxel acquisition.

Gate 2 may:

1. issue one fixed, allow-listed coordinate-only OPeNDAP request;
2. persist the exact raw response, endpoint, byte count and SHA-256;
3. parse the complete `x`, `y` and `z` axes and verify their lengths against the Gate-1 dimensions;
4. verify that every coordinate is finite and each axis is strictly monotonic;
5. determine actual horizontal and vertical spacing from the live axes rather than assuming 100 m / 0.5 m from documentation;
6. map the fixed RD target to a deterministic nominal horizontal cell/index;
7. calculate distance to horizontal cell boundaries and record any neighbour-sensitivity requirement explicitly.

Gate 2 must not:

- request `strat`, `lithok` or any other voxel/model-class values;
- average cells;
- correlate q95 or the monitoring screen with GeoTOP voxels;
- interpret lithology, stratigraphy or hydraulic behaviour;
- infer a confining layer or hydraulic continuity;
- replace BRO ground level with a GeoTOP elevation;
- change the Stage-B decision model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

## Fail-closed conditions for Gate 2

Gate 2 must fail closed on:

- endpoint or query drift away from the exact coordinate-only request;
- missing or extra requested variables;
- malformed coordinate response;
- axis lengths inconsistent with `2646 / 2811 / 313`;
- non-finite values;
- non-monotonic axes;
- ambiguous target mapping that is silently resolved instead of reported;
- any attempt to request categorical/model values in this gate.

Missing or unknown remains missing or unknown.

## Next permitted action

Implement and qualify **coordinate-axis mapping only** on the current branch. Do not request `strat` or `lithok` values until the live coordinate mapping and boundary sensitivity for `GMW000000020774` are independently qualified.