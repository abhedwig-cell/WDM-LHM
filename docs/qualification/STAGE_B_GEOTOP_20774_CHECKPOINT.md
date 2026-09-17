# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **QUALIFIED_GEOTOP_COORDINATE_ACQUISITION_GATE_2A**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12. It acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition and interpretation remain separate.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start and through Gate 2A: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- qualified Gate-1 head: `099ea43a845179df70d811c7826a1a9badad355c`
- qualified Gate-2A head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`
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

Qualified head:

`099ea43a845179df70d811c7826a1a9badad355c`

Qualification:

- ordinary CI run `35188889824`: **PASS**;
- Python 3.10: `93 passed`;
- Python 3.12: `93 passed`;
- live metadata run `35188889782`: **PASS**;
- artifact ID `10483405874`;
- artifact ZIP SHA-256 `5cca45335d6e041cb852d28f0d5f126931584cbca3e522b1066198d3b4b9c62f`;
- DDS SHA-256 `845bf38ef3bcbed025e0a01925508f5f143644c188e9ff703651a85d8fe5ba07`;
- DAS SHA-256 `50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc`.

Declared dimensions:

- `x = 2646`;
- `y = 2811`;
- `z = 313`.

Declared variables include `x`, `y`, `z`, `strat` and `lithok`.

Relevant raw DAS metadata retained from the qualified artifact includes:

- x: `epsg=7415`, units `m`, `standard_name=projection_x_coordinate`, `actual_range=13600.0 278200.0`;
- y: `epsg=7415`, units `m`, `standard_name=projection_y_coordinate`, `actual_range=338500.0 619600.0`;
- z: `epsg=7415`, units `m`, `positive=up`, `reference=NAP`, `actual_range=-50.0 106.5`.

No interpretation of these ranges as cell bounds was admitted in Gate 1.

## Parser reconciliation during Gate 1

Three live-service syntax differences were corrected without changing scientific assumptions:

1. the DAP2 dataset envelope uses a dataset name that must be parsed generically rather than hard-coded to `geotop`;
2. DAP2 Grid structures may repeat coordinate declarations; semantically identical duplicates are deduplicated, conflicting duplicates fail closed;
3. DAS attribute-section indentation is not fixed to exactly two spaces; one-or-more whitespace is accepted while an actual nested section remains required.

## Gate-1 verdict

**QUALIFIED_GEOTOP_METADATA_BOUNDARY**

The dataset identity, dimensions and required variable inventory are pinned. This did not qualify any geological interpretation or change the Stage-B adjudication state of `GMW000000020774_T1`.

## Gate 2A: raw coordinate-axis acquisition

Gate 2A requested exactly the three coordinate variables from the same fixed dataset:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc.ascii?x,y,z`

It did not request `strat`, `lithok` or any categorical/model values and deliberately did not parse or map the target.

Qualified head:

`86ac9581066b73308e30a1f20e14cf38fa88ddd5`

Qualification state on that exact head:

- ordinary CI run `35189463119`: **PASS** on Python 3.10 and 3.12;
- Gate-1 metadata recheck run `35189463139`: **PASS**;
- live coordinate acquisition run `35189463207`: **PASS**;
- all four GitHub checks on the head completed successfully.

Immutable raw coordinate evidence:

- artifact ID `10483422437`;
- artifact name `stage-b-geotop-20774-coordinates-35189463207`;
- artifact ZIP SHA-256 `73545833110b777ae43d4540179d771b43aa074ff158af40f78a57396ead572e`;
- raw ASCII bytes `44455`;
- raw ASCII SHA-256 `de1d362c38b6b3e021955580ad024d764e0f9cb5edc637318b450b63c3ce0b1a`;
- final URL remained exactly the allow-listed `x,y,z` request.

The raw response contains exactly four logical lines: dataset identity followed by complete `x`, `y` and `z` axes.

Observed raw axis facts, not yet used as cell semantics:

- x: 2646 values, `13600` through `278100`, constant increment `100 m`;
- y: 2811 values, `338500` through `619500`, constant increment `100 m`;
- z: 313 values, `-50` through `106`, constant increment `0.5 m`.

The fixed target coordinate is numerically located between successive raw x values `172200` and `172300`, and successive raw y values `447700` and `447800`. Those intervals are not yet called cells until Gate 2B qualifies coordinate semantics.

Gate 2A explicitly preserves:

- `categorical_voxel_values_requested = false`;
- `strat_requested = false`;
- `lithok_requested = false`;
- `coordinate_axes_parsed = false` in the acquisition manifest;
- `point_to_cell_mapping_performed = false`;
- no screen correlation;
- no lithological or hydraulic interpretation;
- no admission decision;
- `allow_admissible_enabled = false`.

## Gate-2A verdict

**QUALIFIED_RAW_GEOTOP_COORDINATE_AXES**

This verdict qualifies the raw x/y/z acquisition and immutable response only. It does not yet qualify point-to-cell mapping or any GeoTOP class value.

## Gate 2B: coordinate semantics and target mapping only

Gate 2B may now parse only the qualified raw x/y/z evidence plus the already qualified Gate-1 DAS metadata.

It may:

1. verify the dataset identity and exact axis membership;
2. verify axis lengths `2646 / 2811 / 313`;
3. reject non-finite or non-monotonic values;
4. derive spacing from the live axes rather than documentation;
5. verify whether the DAS `actual_range` is internally consistent with a deterministic grid-boundary interpretation;
6. verify CRS compatibility before applying the RD target coordinate;
7. map the fixed target to one nominal horizontal index/interval only when coordinate semantics are unambiguous;
8. report exact distance to each horizontal boundary;
9. report ambiguity rather than silently selecting or averaging neighbours.

Gate 2B must not:

- request `strat`, `lithok` or any categorical/model values;
- average neighbouring cells;
- correlate q95 or screen depths to z voxels;
- interpret lithology, stratigraphy or hydraulic behaviour;
- infer a confining layer or hydraulic continuity;
- replace BRO ground level with GeoTOP elevation;
- invent a generic near-boundary threshold merely to force a neighbour decision;
- change the Stage-B decision model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

## Fail-closed conditions for Gate 2B

Fail closed on:

- raw SHA mismatch from the qualified Gate-2A response;
- missing, duplicate or extra axis records;
- length mismatch;
- non-finite values;
- non-monotonic axes;
- coordinate spacing or `actual_range` semantics that are internally inconsistent;
- CRS incompatibility or unresolved CRS meaning;
- a target exactly on a boundary without explicit ambiguity handling;
- any attempt to use categorical GeoTOP values in this gate.

Missing or unknown remains missing or unknown.

## Next permitted action

Implement and qualify **Gate 2B coordinate semantics and target mapping only** on the current branch. Do not request `strat` or `lithok` values until this mapping is independently qualified.