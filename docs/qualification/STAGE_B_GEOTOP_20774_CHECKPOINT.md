# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **QUALIFIED_GEOTOP_COORDINATE_MAPPING_GATE_2B**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12 and acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition, geological interpretation and Stage-B admission remain separate decisions.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main` through Gate 2B: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- PR: #13
- Gate-1 head: `099ea43a845179df70d811c7826a1a9badad355c`
- Gate-2A head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`
- Gate-2B qualified implementation head: `e22babf0dfea9dead8301c50a6bd439400663826`
- parent verdict: `QUALIFIED_LOCAL_BHRG_ACQUISITION_NO_LOCAL_OBJECTS`

## Reused immutable target evidence

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m`
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW, BRO, REGIS or GeoTOP rediscovery is permitted in this workunit.

## Authority and scale boundary

Fixed public GeoTOP authority:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc`

GeoTOP is supporting subregional context, not local well truth. It may not override direct groundwater observations, same-location multi-filter evidence or BRO construction metadata.

## Gate 1: qualified metadata boundary

Verdict: **QUALIFIED_GEOTOP_METADATA_BOUNDARY**

Qualified head: `099ea43a845179df70d811c7826a1a9badad355c`

Evidence:

- ordinary CI run `35188889824`: PASS, `93/93` tests on Python 3.10 and 3.12;
- live metadata run `35188889782`: PASS;
- artifact ID `10483405874`;
- artifact ZIP SHA-256 `5cca45335d6e041cb852d28f0d5f126931584cbca3e522b1066198d3b4b9c62f`;
- DDS SHA-256 `845bf38ef3bcbed025e0a01925508f5f143644c188e9ff703651a85d8fe5ba07`;
- DAS SHA-256 `50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc`.

Pinned dataset contract:

- dimensions: `x=2646`, `y=2811`, `z=313`;
- `strat` and `lithok` are declared as `Int16` grids with dimension order `[x][y][z]`;
- x DAS: `epsg=7415`, units `m`, `actual_range=13600.0 278200.0`;
- y DAS: `epsg=7415`, units `m`, `actual_range=338500.0 619600.0`;
- z DAS: `epsg=7415`, units `m`, `positive=up`, `reference=NAP`, `actual_range=-50.0 106.5`;
- `strat`: `missing_value=0`, `_FillValue=0`;
- `lithok`: `missing_value=-127`, `_FillValue=-127`.

Gate 1 read metadata only. No coordinate values, voxel values, geological interpretation, screen correlation or admission decision were performed.

## Gate 2A: qualified raw coordinate acquisition

Verdict: **QUALIFIED_RAW_GEOTOP_COORDINATE_AXES**

Qualified head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`

Exact request:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc.ascii?x,y,z`

Evidence:

- ordinary CI run `35189463119`: PASS on Python 3.10 and 3.12;
- metadata recheck `35189463139`: PASS;
- live coordinate acquisition `35189463207`: PASS;
- artifact ID `10483422437`;
- artifact ZIP SHA-256 `73545833110b777ae43d4540179d771b43aa074ff158af40f78a57396ead572e`;
- raw ASCII bytes `44455`;
- raw ASCII SHA-256 `de1d362c38b6b3e021955580ad024d764e0f9cb5edc637318b450b63c3ce0b1a`.

Observed axes:

- x: 2646 values, `13600` through `278100`, exact spacing `100 m`;
- y: 2811 values, `338500` through `619500`, exact spacing `100 m`;
- z: 313 values, `-50` through `106`, exact spacing `0.5 m`.

No `strat`, `lithok` or other categorical values were requested.

## Gate 2B: qualified coordinate semantics and mapping

Verdict: **QUALIFIED_GEOTOP_COORDINATE_MAPPING**

Qualified implementation head: `e22babf0dfea9dead8301c50a6bd439400663826`

Qualification on that exact head:

- ordinary CI run `35190008665`: PASS;
- Python 3.10: `111 passed`;
- Python 3.12: `111 passed`;
- metadata recheck run `35190008631`: PASS;
- raw coordinate recheck run `35190008633`: PASS;
- live mapping run `35190008678`: PASS;
- mapping artifact ID `10483407295`;
- mapping artifact ZIP SHA-256 `ddb0e837842a63bb7c68fe9235f3593cd335a97ad7f2af9a0fa26ba969cc26b0`.

The mapping gate independently revalidated the qualified metadata and raw-coordinate SHA boundaries before mapping.

Qualified coordinate semantics:

- compound CRS resolves as `Amersfoort / RD New + NAP height`;
- horizontal CRS resolves to EPSG:28992;
- x/y/z spacing is exactly `100 / 100 / 0.5 m`;
- DAS `actual_range` is consistent with the raw coordinate values representing lower voxel/cell boundaries and an exclusive upper dataset boundary.

Fixed target mapping:

- x zero-based index: `1586`;
- x interval: `[172200, 172300)` m;
- distance to west boundary: `74.997571 m`;
- distance to east boundary: `25.002429 m`;
- y zero-based index: `1092`;
- y interval: `[447700, 447800)` m;
- distance to south boundary: `81.978030 m`;
- distance to north boundary: `18.021970 m`;
- minimum horizontal boundary distance: `18.021970 m`.

No generic near-boundary threshold was invented and no neighbouring cell was averaged or selected. The target is not exactly on a boundary.

Gate 2B explicitly preserved:

- `categorical_voxel_values_requested = false`;
- `strat_requested = false`;
- `lithok_requested = false`;
- no q95/screen-to-z correlation;
- no lithological, stratigraphic or hydraulic interpretation;
- no admission decision;
- `allow_admissible_enabled = false`.

## Next permitted action: Gate 3A raw single-column acquisition

Gate 3A may acquire categorical values for exactly one already-qualified horizontal GeoTOP column at `(x_index=1586, y_index=1092)`.

The first Gate-3 step is acquisition-only. It may request only:

- `strat[1586][1092][0:312]`;
- `lithok[1586][1092][0:312]`.

The constraint expression must remain fixed to those two variables, that one x/y index and the complete qualified z-index range. Raw response bytes, final URL, byte count and SHA-256 must be persisted.

Gate 3A must not:

- request neighbouring x/y columns;
- request probability or uncertainty grids;
- translate class codes to geological names;
- treat missing/fill codes as valid classes;
- correlate the column to q95, ground level or screen depth;
- infer confinement, hydraulic continuity or aquifer membership;
- alter the Stage-B decision model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

Because DAP2 Grid ASCII response structure can include grid-map material, Gate 3A must first preserve and qualify the exact live raw response shape. Parsing and geological interpretation remain later, separate gates.

Fail closed on endpoint/query drift, unexpected requested variables or indices, response-size excess, malformed/empty response, redirects outside the fixed authority, or any attempt to widen the column.

Missing or unknown remains missing or unknown.
