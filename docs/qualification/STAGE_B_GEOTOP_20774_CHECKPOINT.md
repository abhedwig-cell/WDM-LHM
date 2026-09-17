# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **QUALIFIED_GEOTOP_SINGLE_COLUMN_ACQUISITION_GATE_3A**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12 and acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition, parsing, geological interpretation and Stage-B admission remain separate decisions.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main` through Gate 3A: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- PR: #13
- Gate-1 head: `099ea43a845179df70d811c7826a1a9badad355c`
- Gate-2A head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`
- Gate-2B head: `e22babf0dfea9dead8301c50a6bd439400663826`
- Gate-2B checkpoint: `aa185e9b5d424314fe6134193e1d89c49b36c6a1`
- Gate-3A qualified implementation head: `384175e92a026e6511bb7faba26687ab44b3f9aa`
- parent verdict: `QUALIFIED_LOCAL_BHRG_ACQUISITION_NO_LOCAL_OBJECTS`

## Reused immutable target evidence

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m`
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW, BRO, REGIS or GeoTOP rediscovery is permitted in this workunit.

## GeoTOP authority and scale boundary

Fixed public source:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc`

GeoTOP is supporting subregional geological context, not local well truth. It may not override direct groundwater observations, same-location multi-filter evidence or BRO construction metadata.

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
- `strat` and `lithok` are declared `Int16` grids with order `[x][y][z]`;
- x/y/z use EPSG:7415 metadata; z is positive up and referenced to NAP;
- `strat`: `missing_value=0`, `_FillValue=0`;
- `lithok`: `missing_value=-127`, `_FillValue=-127`;
- `strat` long name: `lithostrat`;
- `lithok` long name: `meest waarschijnlijke lithoklasse`.

The qualified DAS does not itself provide a class-code dictionary for translating observed non-missing integer codes to geological names.

## Gate 2A: qualified raw coordinate acquisition

Verdict: **QUALIFIED_RAW_GEOTOP_COORDINATE_AXES**

Qualified head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`

- request: `https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc.ascii?x,y,z`;
- ordinary CI run `35189463119`: PASS on Python 3.10 and 3.12;
- metadata recheck `35189463139`: PASS;
- live coordinate acquisition `35189463207`: PASS;
- artifact ID `10483422437`;
- artifact ZIP SHA-256 `73545833110b777ae43d4540179d771b43aa074ff158af40f78a57396ead572e`;
- raw ASCII bytes `44455`;
- raw ASCII SHA-256 `de1d362c38b6b3e021955580ad024d764e0f9cb5edc637318b450b63c3ce0b1a`.

Observed axes:

- x: 2646 values, `13600` through `278100`, spacing `100 m`;
- y: 2811 values, `338500` through `619500`, spacing `100 m`;
- z: 313 values, `-50` through `106`, spacing `0.5 m`.

## Gate 2B: qualified coordinate semantics and mapping

Verdict: **QUALIFIED_GEOTOP_COORDINATE_MAPPING**

Qualified head: `e22babf0dfea9dead8301c50a6bd439400663826`

- ordinary CI run `35190008665`: PASS;
- Python 3.10: `111 passed`;
- Python 3.12: `111 passed`;
- metadata recheck `35190008631`: PASS;
- raw-coordinate recheck `35190008633`: PASS;
- live mapping run `35190008678`: PASS;
- mapping artifact ID `10483407295`;
- mapping artifact ZIP SHA-256 `ddb0e837842a63bb7c68fe9235f3593cd335a97ad7f2af9a0fa26ba969cc26b0`.

Qualified mapping:

- compound CRS: `Amersfoort / RD New + NAP height`;
- horizontal CRS: EPSG:28992;
- x zero-based index: `1586`, interval `[172200, 172300)` m;
- y zero-based index: `1092`, interval `[447700, 447800)` m;
- distance to west/east boundary: `74.997571 / 25.002429 m`;
- distance to south/north boundary: `81.978030 / 18.021970 m`;
- minimum horizontal boundary distance: `18.021970 m`.

No generic near-boundary threshold was invented and no neighbouring cell was averaged or silently selected.

## Gate 3A: qualified raw single-column acquisition

Verdict: **QUALIFIED_RAW_GEOTOP_SINGLE_COLUMN**

Qualified implementation head: `384175e92a026e6511bb7faba26687ab44b3f9aa`

Exact request:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc.ascii?strat[1586:1:1586][1092:1:1092][0:1:312],lithok[1586:1:1586][1092:1:1092][0:1:312]`

Qualification on that exact head:

- ordinary CI run `35191379621`: PASS;
- Python 3.10: `124 passed`;
- Python 3.12: `124 passed`;
- metadata recheck run `35191379591`: PASS;
- coordinate acquisition recheck run `35191379608`: PASS;
- mapping recheck run `35191379598`: PASS;
- live single-column run `35191379732`: PASS;
- artifact ID `10483673552`;
- artifact name `stage-b-geotop-20774-column-35191379732`;
- artifact ZIP SHA-256 `d8d5fc3357bd8cf861d673507befa0ea8a3e8bcdd9933f03b3acffd52b6e719b`;
- raw ASCII bytes `6221`;
- raw ASCII SHA-256 `ad7acee0b57acd428f6df3d7dd6104d94c267a7ddc11b65798446db7dfebb0a8`.

The raw live response contains:

- one `strat.z` axis of 313 values;
- one `strat.strat[strat.x=172200][strat.y=447700]` value vector;
- one `lithok.z` axis of 313 values;
- one `lithok.lithok[lithok.x=172200][lithok.y=447700]` value vector.

The returned x/y labels agree with the Gate-2B lower-bound coordinate mapping. Gate 3A does not yet admit the class-vector contents as interpreted geology.

The raw vectors contain the metadata-defined missing tokens `strat=0` and `lithok=-127`. These tokens must become missing/null in any later parser. They must never be treated as valid geological classes or replaced by another default.

Gate 3A explicitly preserved:

- exactly one horizontal column;
- exactly `strat` and `lithok`;
- full z-index range `0:312`;
- no probability or uncertainty grids;
- no neighbour columns;
- `response_parsed = false`;
- `class_codes_interpreted = false`;
- no q95/screen correlation;
- no lithological or hydraulic interpretation;
- no admission decision;
- `allow_admissible_enabled = false`.

## Next permitted action: Gate 3B structural parser only

Gate 3B may parse only the immutable Gate-3A raw response plus already qualified Gate-1/Gate-2 evidence.

It may:

1. require raw SHA-256 `ad7acee0b57acd428f6df3d7dd6104d94c267a7ddc11b65798446db7dfebb0a8`;
2. require exactly the four expected data records and no extra variable records;
3. require both z vectors to contain exactly 313 values and to equal the qualified Gate-2 z axis;
4. require both class vectors to contain exactly 313 integer values;
5. require the returned x/y labels to equal `172200 / 447700` for both variables;
6. normalize only metadata-authorized missing tokens: `strat 0 -> null`, `lithok -127 -> null`;
7. persist parsed integer-or-null vectors and structural provenance.

Gate 3B must not:

- map non-missing `strat` or `lithok` codes to geological names;
- request or use probability/uncertainty grids;
- correlate z positions with q95, ground level or the monitoring screen;
- infer lithology, stratigraphy, confinement, permeability or hydraulic continuity;
- change the Stage-B adjudication model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

Fail closed on SHA mismatch, record-name drift, duplicate/extra records, length mismatch, z-axis mismatch, x/y-label mismatch, non-integer class values or any unqualified missing-value substitution.

Missing or unknown remains missing or unknown.
