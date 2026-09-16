# Stage-B REGIS raw hydro-column checkpoint

Status: **QUALIFIED_RAW_HYDRO_ACQUISITION**

Date: 2026-09-16

## Capability

This checkpoint qualifies bounded acquisition of raw REGIS II v02r2s3 hydrogeological values for exactly three fixed pilot columns. It admits acquisition evidence only. It does not yet admit parsing, screen-to-unit mapping, hydrogeological interpretation or `ADMISSIBLE_FREATIC`.

## Canonical state

- repository: `abhedwig-cell/WDM-LHM`
- branch: `work/regis-point-columns`
- acquisition implementation head: `2963dc09766d5058aea03aa68dc650952aa53637`
- coordinate checkpoint head: `4727b1efe09c6ed31a723822b034b4caf5e2f1f3`
- base `main`: `d88c2ac976010ddc165ef05c76c6158fb0016e28`
- dataset: `https://www.dinodata.nl/opendap/REGIS/REGIS.nc`
- version: `REGIS v02r2s3`
- CRS: `EPSG:28992`

## Qualified request scope

Columns:
1. `4074_nominal`: x index `1703`, y index `1407`
2. `4074_west_boundary_sensitivity`: x index `1702`, y index `1407`
3. `4104_nominal`: x index `1696`, y index `1415`

Each request contains all 132 layers and exactly:
- `top`
- `bottom`
- `kh`
- `kv`
- `c`

Explicitly excluded from independent Stage-B evidence acquisition:
- `freatisch`
- `kD`
- `hgv`
- `sdh`
- `sdv`

`kD` remains excluded because the package-exact REGIS authority defines it over the saturated thickness, while the admitted REGIS freatic-surface lineage is largely LHM-derived.

## Qualification

Targeted synthetic hydro-acquisition tests: **4/4 PASS** before repository CI. A test exposed and then closed a guardrail gap: maximum response size is checked again after an injected transport returns, not only inside the default HTTP transport.

Ordinary CI run `35132810447`: **PASS** on Python 3.10 and 3.12.

Live raw-hydro workflow run `35132969090`: **PASS**.

Artifact:
- ID `10461739661`
- name `regis-hydro-probe-35132969090`
- ZIP size `10364` bytes
- artifact digest SHA-256 `6d06a51036e23f7dbbe7ec3636b5998435d64f2872eebd8a0eb07b6eb71e2695`

Raw responses:
- `4074_nominal`: `32083` bytes, SHA-256 `fbb7cf9bf77abbb268fb9cf38f709ee400923693f165e5d292f656f0e5bfc2aa`
- `4074_west_boundary_sensitivity`: `32080` bytes, SHA-256 `79a6c28d741bd5993a56475b117e95c69903ac1e4d506e504b394886cb53356c`
- `4104_nominal`: `32086` bytes, SHA-256 `9bbab4688d86aec9d62788de411a29ce86fbae9d6a0f247c831d15a722ff6560`

Total retained raw response bytes: `96249`.

All three responses report `Last-Modified: Fri, 20 Dec 2024 03:48:35 GMT`.

## Observed raw format

The server returns DAP2 ASCII text. For each requested variable it emits one x-coordinate record followed by 132 layer records, for example:

`top.x, 170300`

`top.top[top.layer="NUBXz2"][top.y=440700], 8.15`

The server orders the returned variable blocks as `top`, `bottom`, `c`, `kh`, `kv`; parsing must therefore be name-based and must not depend on request order.

Each variable block contains exactly 132 layer-labelled rows in the live evidence.

## Missing-value evidence

The live REGIS OPeNDAP responses use the exact token `-9999` for unavailable layer/attribute values. This is consistent with the documented TNO raster convention for the national DGM/REGIS II/GeoTOP grids, where `-9999` is the standard NoData value for the 2800 x 3250, 100 m national grid.

The next parser may map **only the exact token `-9999`** to missing/null. It must not convert missing values to zero, interpolate them, infer favourable hydrogeology from them, or apply generic numerical clipping.

## Initial non-interpretive counts

All three columns contain:
- 132 rows for each of `top`, `bottom`, `kh`, `kv`, `c`;
- 22 non-missing `top` values;
- 21 non-missing `bottom` values;
- 15 non-missing `kh` values;
- 6 non-missing `kv` values;
- 6 non-missing `c` values.

These counts describe data presence only. They are not yet an interpretation of aquifers, aquitards or screen suitability.

## Boundary-sensitivity observation

The two 4074 columns have the same live layer-label structure but differ in shallow geometric values. This demonstrates that the previously qualified 5.6 mm proximity to the x-grid boundary is materially relevant to the pilot and must not be averaged away.

No hydrogeological conclusion is admitted from that difference at this checkpoint.

## Verdict

**PASS — bounded raw REGIS hydro-column acquisition is qualified.**

## Mutations admitted

- `src/wdm_lhm/regis_hydro_probe.py`
- `src/wdm_lhm/regis_hydro_probe_cli.py`
- `tests/test_regis_hydro_probe.py`
- `.github/workflows/regis-hydro-probe.yml`

After this checkpoint the raw-acquisition workflow is retained as manual-only qualification machinery.

## Next permitted action

Implement and synthetically qualify a parser pinned to the three admitted raw SHA-256 values. Requirements:
- parse by variable/layer names, not block order;
- require exactly 132 rows for each required variable;
- require consistent layer labels and y coordinate within one response;
- preserve raw provenance;
- map exact `-9999` to missing/null only;
- fail closed on malformed, duplicate, missing, non-numeric or unexpected records;
- produce a compact structured column artifact;
- perform no screen-to-unit mapping or Stage-B admission yet.

## Exclusions

This checkpoint does not:
- admit parsed hydrogeological columns;
- interpret layer-code semantics;
- map monitoring screens to REGIS units;
- infer absence of a confining unit from NoData;
- average the 4074 nominal and neighbour columns;
- define a generic spatial-boundary or vertical-gradient threshold;
- use `freatisch` or `kD` as independent evidence against LHM;
- assign `ADMISSIBLE_FREATIC`.
