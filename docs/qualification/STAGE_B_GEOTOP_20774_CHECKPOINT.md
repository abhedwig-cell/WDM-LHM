# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **QUALIFIED_GEOTOP_SINGLE_COLUMN_PARSE_GATE_3B**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12 and acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition, parsing, geological interpretation and Stage-B admission remain separate decisions.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main` through Gate 3B qualification: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- PR: #13
- Gate-1 head: `099ea43a845179df70d811c7826a1a9badad355c`
- Gate-2A head: `86ac9581066b73308e30a1f20e14cf38fa88ddd5`
- Gate-2B head: `e22babf0dfea9dead8301c50a6bd439400663826`
- Gate-2B checkpoint: `aa185e9b5d424314fe6134193e1d89c49b36c6a1`
- Gate-3A head: `384175e92a026e6511bb7faba26687ab44b3f9aa`
- Gate-3A checkpoint: `45dab4f143347379aea0037fa4d1b411b9adcb53`
- Gate-3B qualified implementation head: `b38e4f06bb11621138bfa36d813ac330931e83de`
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

The raw live response contains one `strat` vector and one `lithok` vector of 313 values, each accompanied by the same 313-value z axis. Returned x/y labels are `172200 / 447700` and agree with the Gate-2B lower-bound mapping.

The raw vectors contain the metadata-defined missing tokens `strat=0` and `lithok=-127`. Those tokens are not valid classes and may only become missing/null.

## Gate 3B: qualified structural parser

Verdict: **QUALIFIED_GEOTOP_SINGLE_COLUMN_PARSE_CODES_UNINTERPRETED**

Qualified implementation head: `b38e4f06bb11621138bfa36d813ac330931e83de`

Qualification on that exact head:

- ordinary CI run `35200195214`: PASS;
- Python 3.10: `132 passed`;
- Python 3.12: `132 passed`;
- metadata recheck run `35200195311`: PASS;
- coordinate acquisition recheck run `35200195035`: PASS;
- coordinate mapping recheck run `35200194993`: PASS;
- single-column acquisition recheck run `35200195119`: PASS;
- live structural parser run `35200195165`: PASS;
- parser artifact ID `10487850489`;
- artifact name `stage-b-geotop-20774-column-parse-35200195165`;
- artifact ZIP SHA-256 `cc90a4ceaf7d79efdd16205b31c73730a4ac27effcd9391b87ee465221123c5e`.

Gate 3B reacquired the raw Gate-3A response and required raw SHA-256:

`ad7acee0b57acd428f6df3d7dd6104d94c267a7ddc11b65798446db7dfebb0a8`

before parsing.

Qualified structural result:

- vector count: `313`;
- `strat` missing count after exact `0 -> null`: `192`;
- `lithok` missing count after exact `-127 -> null`: `192`;
- distinct non-missing `strat` codes: `[1000, 3030, 3100, 4100, 5000, 5120]`;
- distinct non-missing `lithok` codes: `[0, 1, 2, 3, 5, 6, 7]`.

The parser deliberately preserves `lithok=0` as a non-missing integer code because the qualified DAS defines only `-127` as missing for `lithok`. Likewise, no unqualified token is converted to missing or to another default.

The parser verifies:

- exact raw SHA;
- exact dataset and record structure;
- exact x/y labels `172200 / 447700`;
- both 313-element z vectors against the qualified Gate-2 z axis;
- both 313-element class vectors as integers;
- metadata-authorized missing normalization only.

Gate 3B explicitly does not:

- translate any non-missing code to a geological name;
- use probability or uncertainty grids;
- correlate voxels with q95, BRO ground level or the monitoring screen;
- infer lithology, stratigraphy, permeability, confinement or hydraulic continuity;
- alter the Stage-B decision model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

## Workunit verdict

**QUALIFIED_GEOTOP_ACQUISITION_AND_STRUCTURAL_PARSE_CODES_UNINTERPRETED**

The bounded GeoTOP acquisition and structural parser are qualified. They establish reproducible local subregional context for one fixed GeoTOP column, but they do not yet establish the semantic meaning of the observed integer class codes. The qualified dataset metadata does not itself supply a codebook. Therefore this workunit stops before geological interpretation.

`GMW000000020774_T1` remains not positively admitted by this evidence. No inference of free hydraulic continuity, confining behaviour or freatic representativeness follows from the raw integer codes alone.

## Exclusions retained

- no neighbouring GeoTOP columns;
- no probability or uncertainty grids;
- no silent interpolation or averaging;
- no code meaning inferred from integer magnitude or naming convention;
- no q95/screen/ground-level correlation in this workunit;
- no replacement of BRO ground level;
- no hydraulic-property inference from categorical codes alone;
- no Stage-B positive admission;
- no expansion to the full GMW population.

## Next permitted action

Close this acquisition/parser workunit after its checkpoint head is requalified and merged.

A subsequent, separate scientific decision surface may perform a targeted authority check for an official GeoTOP 1.6.1 class-code dictionary covering the observed `strat` and `lithok` codes. Only an explicit, version-compatible authority may permit semantic code translation. If such authority is absent, ambiguous or version-incompatible, the semantic interpretation must fail closed and the codes remain uninterpreted.
