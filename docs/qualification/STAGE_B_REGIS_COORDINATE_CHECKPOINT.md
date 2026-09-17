# Stage-B REGIS coordinate mapping checkpoint

Status: **QUALIFIED_COORDINATE_MAPPING**

Date: 2026-09-16

## Capability

This checkpoint qualifies the REGIS II v02r2s3 grid-coordinate evidence and deterministic mapping of the two TS07 Wageningen GMW locations to explicit REGIS `x_bounds` / `y_bounds`.

It does not yet acquire hydrogeological model values and does not make a Stage-B freatic-admission decision.

## Canonical state

- repository: `abhedwig-cell/WDM-LHM`
- source branch: `work/regis-point-columns`
- qualified implementation head: `be8689cdf0e577978c5932eedbc7cc7de6072313`
- canonical base at workunit start: `main` `d88c2ac976010ddc165ef05c76c6158fb0016e28`
- parent capability: qualified REGIS OPeNDAP metadata / identity from run `35127716984`
- dataset: `https://www.dinodata.nl/opendap/REGIS/REGIS.nc`
- version: `REGIS v02r2s3`
- CRS: `EPSG:28992`

## Immutable dependencies

Qualified metadata:
- DDS SHA-256 `298867cee98c3811a925aa47614d67484336f402b8a58bed492020cb4dfbd3af`
- DAS SHA-256 `1c14a662273eb0d30c945cee6030ae1a7bd7d484baeef09cd56dd8d06f25a173`

Qualified coordinate evidence:
- raw DAP2 ASCII SHA-256 `fa39271a98fefa2091483b7247d53e3744e1e26e478969310ce6f3560725c7f3`
- raw bytes `231772`
- variables exactly `x`, `y`, `x_bounds`, `y_bounds`, `layer`
- dimensions `x=2800`, `y=3250`, `layer=132`

## Qualification

Ordinary CI run `35132034918`: **PASS** on Python 3.10 and 3.12.

Targeted synthetic mapping tests: **6/6 PASS** before repository CI. They cover:
- exact parsing of the TNO DAP2 ASCII shape;
- explicit-bound rather than assumed-center mapping;
- fail-closed detection of non-contiguous bounds;
- exact internal-boundary ambiguity;
- near-boundary distance reporting without a universal tolerance;
- the two fixed TS07 target mappings and raw-evidence hash pinning.

Live coordinate/mapping run `35132157424`: **PASS**.

Artifact:
- ID `10461443564`
- name `regis-coordinate-probe-35132157424`
- ZIP size `64424` bytes
- artifact digest SHA-256 `4c21531c95ee9fc1870fbf4ad34ed6d7e8eac5be75c061afd39788675eb2e405`

Artifact members:
- `regis_coordinate_manifest.json`
- `regis_coordinate_response.ascii.txt`
- `regis_coordinate_mapping.json`

Mapping manifest SHA-256: `58596e715f335563f8654bf99ba4dcee190f7668ed9d76e1aa1ae37b5fd3389a`.

## Qualified target mapping

### GMW000000004074

TS07 RD coordinate:
- x `170300.00558661332` m
- y `440749.9888647009` m

Nominal REGIS cell from explicit bounds:
- x index `1703`, bounds `[170300, 170400]`
- y index `1407`, bounds `[440700, 440800]`

Boundary evidence:
- distance to western x boundary `170300`: **0.00558661332 m**
- adjacent x cell across that boundary: index `1702`
- y-boundary distances are approximately 50 m and are not comparably sensitive.

The official coordinate is therefore inside x cell 1703, not exactly on the boundary, but only 5.6 mm from the west boundary. This checkpoint does not introduce a generic near-boundary threshold. For this known pilot case the next hydrogeological acquisition must preserve the sensitivity explicitly by reading both x=1703 and adjacent x=1702 at y=1407.

### GMW000000004104

TS07 RD coordinate:
- x `169680.00087220868` m
- y `441579.98838886514` m

Nominal REGIS cell from explicit bounds:
- x index `1696`, bounds `[169600, 169700]`
- y index `1415`, bounds `[441500, 441600]`

Nearest boundary distances:
- x: `19.99912779132` m
- y: `20.01161113486` m

No additional neighbour is required by this pilot-specific coordinate-boundary diagnostic.

## Boundary semantics

Mapping is based only on the qualified `x_bounds` and `y_bounds`. The coordinate arrays themselves are not assumed to be cell centres.

If a coordinate lies exactly on an internal grid boundary, the implementation returns both adjacent candidate cells and `index=None`. It does not silently choose a half-open convention.

If a coordinate lies inside a cell, the implementation reports the exact distances to both bounds and the adjacent cell across the nearest boundary. It does not classify a near-boundary point through a universal tolerance.

## Scientific lineage constraint for the next phase

The package-exact REGIS documentation states that `kD` is transmissivity over the saturated part and that saturated thickness uses the REGIS freatic groundwater level. Because the admitted REGIS freatic-surface lineage is largely LHM-derived, `kD` is not admitted as independent evidence against LHM in this Stage-B pilot.

The next acquisition is therefore limited to:
- `top`
- `bottom`
- `kh`
- `kv`
- `c`

`freatisch`, `kD`, `hgv`, `sdh`, and `sdv` remain outside the independent Stage-B evidence request.

## Verdict

**PASS — REGIS coordinate parsing, explicit-bound cell mapping and pilot boundary sensitivity are qualified.**

## Mutations admitted by this checkpoint

- `src/wdm_lhm/regis_grid_mapping.py`
- `src/wdm_lhm/regis_grid_mapping_cli.py`
- `tests/test_regis_grid_mapping.py`
- coordinate workflow extended to reproduce the qualified raw SHA and emit/validate the mapping manifest

After this checkpoint the coordinate workflow is retained as manual-only immutable qualification machinery; it is no longer the automatic next-phase trigger.

## Next permitted action

Implement a separate bounded raw hydrogeological point-column acquisition on the same branch for exactly three columns:
1. `4074_nominal`: `(x=1703, y=1407)`
2. `4074_west_boundary_sensitivity`: `(x=1702, y=1407)`
3. `4104_nominal`: `(x=1696, y=1415)`

For each column request all 132 layers but only `top`, `bottom`, `kh`, `kv`, and `c`. Retain raw responses and hashes first. Do not yet map monitoring screens to units, infer confining conditions, or assign `ADMISSIBLE_FREATIC` until the live response format and missing-value semantics are qualified.

## Exclusions

This checkpoint does not:
- request or interpret hydrogeological point values;
- use REGIS `freatisch` as independent evidence;
- use `kD` as independent evidence against LHM;
- infer absence of a unit from missing data;
- define a universal spatial-boundary or vertical-gradient threshold;
- change Stage-B evidence weights;
- assign `ADMISSIBLE_FREATIC`.
