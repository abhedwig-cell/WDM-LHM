# Stage-B REGIS OPeNDAP point-column workunit

## Purpose

Acquire hydrogeological REGIS II context for exactly the two admitted TS07 Wageningen multi-filter cases without reopening the full 1.18 GB archive chain and without treating the REGIS freatic surface as independent LHM validation evidence.

Targets are fixed by the qualified TS07 live artifact (`freatic-smoke-35109465960`, artifact `10452120627`):

| GMW | RD x (m) | RD y (m) | ground level (m NAP) |
|---|---:|---:|---:|
| `GMW000000004074` | 170300.00558661332 | 440749.9888647009 | 7.93 |
| `GMW000000004104` | 169680.00087220868 | 441579.98838886514 | 9.81 |

The two filters within one GMW share the same spatial column. Filter screen elevations and observed vertical-head evidence remain those admitted by `TS07_CHECKPOINT.md`.

## Admitted dependencies

Canonical source state at workunit start:
- `main` commit `d88c2ac976010ddc165ef05c76c6158fb0016e28`;
- package-exact REGIS II v2.2.3 documentation authority admitted by PR #8;
- recursive REGIS archive chain and hashes admitted by `STAGE_B_REGIS_RECURSIVE_INVENTORY.md`;
- formal raster semantics admitted by `STAGE_B_REGIS_DOCUMENT_AUTHORITY.md`.

Public service authority:
- DINOloket documents TNO OPeNDAP as an official distribution route for REGIS II NetCDF and supports subsetting an area of interest: `https://www.dinoloket.nl/en/modelbestanden-aanvragen/netcdf`.

## Scientific lineage constraint

`freatisch.img` / the REGIS freatic surface is not independent evidence against LHM because its REGIS II v2.2 production lineage is largely LHM-derived. This workunit therefore does not use the freatic surface to validate LHM or to declare a tube `ADMISSIBLE_FREATIC`.

The intended REGIS contribution is hydrogeological geometry and hydraulic context: unit tops/bases, presence/absence of units, and where available `kh`, `kv`, `c`, and saturated `kD` semantics.

## Phase 1 — OPeNDAP metadata discovery

### Qualification boundary

Phase 1 may request only HTML catalog pages and DAP2 DDS/DAS metadata. It may not request `.ascii`, `.dods`, NetCDF payloads, raster values or point-column values.

### Synthetic qualification

Ordinary CI passed on Python 3.10 and 3.12 before both live attempts. The targeted probe tests establish bounded response sizes, same-service navigation, DAP metadata discovery, rejection of unavailable roots, and the invariant that no value request is performed.

### Live attempt 1 — fail closed

Workflow run `35127198473` on head `f8a0386e24e5f259a8b6f53cbab2e752e49c5f19` failed before HTTP response processing with:

`SSLCertVerificationError: certificate verify failed: Hostname mismatch, certificate is not valid for 'dinodata.nl'`.

No TLS verification was disabled. No REGIS value request was made and no evidence artifact was admitted from this failed attempt.

The public OPeNDAP service is TLS-valid at `https://www.dinodata.nl/opendap/`. The acquisition root was corrected to that host and a regression test pins the TLS-valid default.

### Live attempt 2 — PASS

Corrected head: `9524c25dcc0a92e94054c1941c4133e8dfd2460b`

Ordinary CI run `35127597590`: PASS on Python 3.10 and 3.12.

Live OPeNDAP metadata workflow run `35127716984`: **PASS**.

Artifact:
- ID `10460111599`;
- name `regis-opendap-probe-35127716984`;
- ZIP size `50,637` bytes;
- artifact digest SHA-256 `07c47c21d5b09608415b98eef2615ed30313c445f57f883899ecfe9f75d914f5`.

Manifest counts:
- HTML/catalog pages retained: `16`;
- REGIS dataset candidates: `1`;
- candidates exposing both DDS and DAS: `1`;
- candidates with v02r2s3 identity: `1`;
- total retained response bytes before ZIP compression: `981,500`.

The generic root crawl encountered bounded errors on unrelated DGM/GeoTOP/NL3D CovJSON links. These did not affect the sole REGIS candidate or its DDS/DAS evidence. Subsequent phases shall use the now-qualified fixed REGIS dataset URL and shall not repeat the broad catalog crawl.

### Admitted dataset identity and metadata

Qualified dataset URL:

`https://www.dinodata.nl/opendap/REGIS/REGIS.nc`

DDS:
- bytes `2,300`;
- SHA-256 `298867cee98c3811a925aa47614d67484336f402b8a58bed492020cb4dfbd3af`.

DAS:
- bytes `6,658`;
- SHA-256 `1c14a662273eb0d30c945cee6030ae1a7bd7d484baeef09cd56dd8d06f25a173`.

The DAS explicitly identifies both `project` and `title` as `REGIS v02r2s3`, matching the package-exact REGIS II v2.2.3 authority. It also identifies the grid CRS as `EPSG:28992`.

The DDS admits these dimensions:
- `x = 2800`;
- `y = 3250`;
- `layer = 132`.

The DDS/DAS admit the following relevant variables and units:
- `top[layer,y,x]`, m-NAP;
- `bottom[layer,y,x]`, m-NAP;
- `kD[layer,y,x]`, m2/day;
- `c[layer,y,x]`, days;
- `kh[layer,y,x]`, m/day;
- `kv[layer,y,x]`, m/day;
- `sdh[layer,y,x]`, m/day;
- `sdv[layer,y,x]`, m/day;
- coordinate arrays `x`, `y`, `x_bounds`, `y_bounds`;
- string coordinate `layer[132]`.

The global metadata states that REGIS unit top/base/thickness grids are mapped at 100 x 100 m resolution. Phase 1 does not infer cell centers or indices from that statement alone.

All live guardrail flags remained false:
- value requests;
- DAP2 `.dods` requests;
- DAP2 `.ascii` requests;
- NetCDF payload download;
- hydrogeological interpretation;
- admission decision.

## Phase-1 verdict

**PASS — REGIS OPeNDAP metadata and dataset identity qualified.**

This admits the service endpoint, version identity, CRS, dimensions, variable names and stated units. It admits no REGIS model value and no local hydrogeological conclusion.

## Phase 2 — exact two-point column extraction

Full hydrogeological point values are not yet permitted. The next bounded subphase is coordinate qualification only.

Before requesting `top`, `bottom`, `kh`, `kv`, `c` or `kD`, the workunit shall:
1. acquire only the compact `x`, `y`, `x_bounds`, `y_bounds` and `layer` coordinate variables from the qualified fixed dataset URL;
2. retain exact response provenance and hashes;
3. prove deterministic cell lookup including boundary behaviour with synthetic tests;
4. persist each target RD coordinate, resolved x/y index and exact cell bounds/center;
5. preserve missing coordinate information as missing rather than imputing it.

Only after that coordinate checkpoint may the same two x/y cells be queried for the minimum hydrogeological variables required to map the qualified TS07 screen elevations to REGIS units.

## Exclusions

This checkpoint does not:
- read REGIS hydrogeological model values;
- interpret local confining conditions;
- map screens to hydrogeological units;
- infer absence of a confining unit from missing data;
- define a universal vertical-gradient threshold;
- use `freatisch` as independent evidence;
- change Stage-B evidence weights;
- assign `ADMISSIBLE_FREATIC`.

## Current status

`PHASE_1_QUALIFIED / PHASE_2_COORDINATE_QUALIFICATION_NEXT`

## Next permitted action

Implement and synthetically qualify a bounded coordinate-only OPeNDAP acquisition against the fixed qualified `REGIS.nc` endpoint. Persist a coordinate checkpoint before any hydrogeological point values are requested.
