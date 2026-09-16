# Stage-B REGIS parsed hydro-column checkpoint

Status: **QUALIFIED_PARSED_HYDRO_COLUMNS**

Date: 2026-09-16

## Capability

This checkpoint qualifies deterministic parsing of the three previously admitted raw REGIS II v02r2s3 hydrogeological point columns. It admits structured `top`, `bottom`, `kh`, `kv`, and `c` values with explicit missing-data semantics and immutable raw provenance.

It does not yet admit screen-to-unit mapping, aquifer/aquitard interpretation or `ADMISSIBLE_FREATIC`.

## Canonical state

- repository: `abhedwig-cell/WDM-LHM`
- branch: `work/regis-point-columns`
- parser implementation head: `62d85993531baf902f4eeff39b8f1f9222d11a01`
- raw hydro checkpoint head: `6bf0b9a288a73d2f7eefe7d4d82cfdef2eafdc0e`
- coordinate checkpoint head: `4727b1efe09c6ed31a723822b034b4caf5e2f1f3`
- base `main`: `d88c2ac976010ddc165ef05c76c6158fb0016e28`

## Immutable raw dependencies

Raw-hydro acquisition run `35132969090`, artifact `10461739661`, artifact digest SHA-256 `6d06a51036e23f7dbbe7ec3636b5998435d64f2872eebd8a0eb07b6eb71e2695`.

Pinned raw responses:
- `4074_nominal`: SHA-256 `fbb7cf9bf77abbb268fb9cf38f709ee400923693f165e5d292f656f0e5bfc2aa`
- `4074_west_boundary_sensitivity`: SHA-256 `79a6c28d741bd5993a56475b117e95c69903ac1e4d506e504b394886cb53356c`
- `4104_nominal`: SHA-256 `9bbab4688d86aec9d62788de411a29ce86fbae9d6a0f247c831d15a722ff6560`

## Parser contract

The parser:
- is variable-name based and does not depend on server block order;
- requires dataset label `REGIS.nc`;
- requires exactly one x-coordinate record for each of `top`, `bottom`, `kh`, `kv`, `c`;
- requires one consistent y-coordinate inside each block and across all blocks;
- requires exactly 132 layer-labelled rows per variable;
- requires identical layer labels and layer order across all five variables and all three columns;
- rejects duplicate, missing, unknown, malformed and non-finite records;
- maps only the exact raw token `-9999` to null;
- never converts null to zero, fills a gap, clips an unexpected value or infers a unit from missing data.

The exact-token rule is intentional. A numerically similar but different token such as `-9999.0` is not silently reclassified by the parser; unexpected service representation drift must be reviewed rather than normalized away.

## Qualification

Ordinary CI run `35133615395`: **PASS** on Python 3.10 and 3.12.

Live parse-qualification run `35133740381`: **PASS**.

The run first reacquired the three point columns and reproduced all three admitted raw SHA-256 values before parsing.

Artifact:
- ID `10462726147`
- name `regis-hydro-parse-35133740381`
- ZIP size `13952` bytes
- artifact digest SHA-256 `161db617615778463ae91a0e7f0ede23b382a6c3ca20e3f4266e1664c38d512e`

Structured artifact:
- `regis_hydro_columns.json`
- size `67874` bytes
- SHA-256 `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`

Reacquired raw manifest SHA-256: `e4513ed8f44dd3ab8d6287496978290f6c2d52e8ba95806d23e1b79c34bcb89c`.

## Parsed live invariants

Each column contains exactly 132 rows and the same layer labels.

For each of the three columns the non-missing counts are:
- `top`: 22
- `bottom`: 21
- `kh`: 15
- `kv`: 6
- `c`: 6

Coordinates reproduced by the live parser:
- `4074_nominal`: x `170300`, y `440700`
- `4074_west_boundary_sensitivity`: x `170200`, y `440700`
- `4104_nominal`: x `169600`, y `441500`

These are dataset coordinate-array values for the qualified indices. Pilot point-to-cell membership itself remains defined by the previously qualified explicit `x_bounds` / `y_bounds`, not by interpreting these coordinate values as cell centres.

## Missing-value evidence

The live service again reproduced exact `-9999` tokens in the same raw files. The parser represents those tokens as JSON null.

This is consistent with the TNO national raster convention in which `-9999` is the NoData value for the 2800 x 3250, 100 m DGM/REGIS II/GeoTOP grid. This checkpoint uses that only to define data absence; it does not interpret what a missing hydraulic property means physically.

## Adjacent scientific caveat, not yet applied as a decision

The current TNO REGIS II v2.2.3 metadata records a known issue with the mapped extent of `NUgsc` along the west flank of the Oost-Veluwe: the `NUgsc` boundary should lie farther west, with related units to be adjusted in a future update.

Source: TNO/BRO metadata for HGM000000000062 and the current REGIS II v2.2.3 model-unit documentation.

This checkpoint does **not** assert that either Wageningen GMW falls inside the documented affected polygon/area. The caveat is retained for the later interpretation stage and reinforces the existing rule that REGIS is regional supporting evidence, not exact local truth.

## Verdict

**PASS — deterministic parsing and missing-data handling for the three qualified REGIS hydro columns are admitted.**

## Mutations admitted

- `src/wdm_lhm/regis_hydro_parse.py`
- `src/wdm_lhm/regis_hydro_parse_cli.py`
- `tests/test_regis_hydro_parse.py`
- `.github/workflows/regis-hydro-parse.yml`

After this checkpoint the parse-qualification workflow is retained as manual-only qualification machinery.

## Next permitted action

Implement a separate geometric screen-overlap capability using only:
- the qualified TS07 ground-level and screen-depth metadata;
- the admitted parsed `top` / `bottom` geometry;
- exact interval arithmetic.

Required screen elevations in m NAP:
- `4074/tube1`: top `5.72`, bottom `2.72`
- `4074/tube2`: top `-3.16`, bottom `-3.66`
- `4104/tube1`: top `-2.21`, bottom `-4.21`
- `4104/tube2`: top `-26.17`, bottom `-28.17`

The overlap capability may report which REGIS layer intervals geometrically intersect each screen and by how many metres. It must:
- preserve 4074 nominal and west-neighbour results separately;
- ignore no layer merely because a hydraulic property is null;
- make no aquifer/aquitard classification from layer-code suffixes until those semantics are independently reconciled;
- make no freatic-admission decision.

## Exclusions

This checkpoint does not:
- classify REGIS units as aquifer, aquitard or freatic system;
- map screens semantically beyond geometric interval intersection;
- infer favourable conditions from null `kh`, `kv` or `c`;
- average the two 4074 columns;
- resolve the known `NUgsc` regional-model caveat;
- change Stage-B evidence weights;
- assign `ADMISSIBLE_FREATIC`.
