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

## Bounded execution

### Phase 1 — OPeNDAP metadata discovery

Before any model value is read:
1. crawl only the official OPeNDAP directory/catalog below `/opendap/`;
2. discover REGIS dataset candidates;
3. request only DAP2 DDS/DAS metadata for candidates;
4. persist URL, response hashes, dimensions/variable metadata source text and compact provenance;
5. do **not** request `.ascii`, `.dods`, NetCDF payloads or any raster/column value.

Qualification requires at least one REGIS dataset candidate exposing both DDS and DAS. Dataset version, CRS, dimensions and variable semantics must then be reconciled to the package-exact v2.2.3 authority before Phase 2.

### Phase 2 — exact two-point column extraction

Not yet permitted. After Phase 1 qualification, a later commit on this same workunit may implement a bounded value request only if:
- the live dataset is demonstrably the intended REGIS II version or an explicitly reconciled equivalent;
- EPSG/RD coordinate semantics are explicit;
- grid indexing is deterministic and tested at cell boundaries;
- missing values remain missing;
- only the variables needed for hydrogeological column context are requested;
- both target coordinates and resolved cell centers are persisted;
- `freatisch` is excluded from independent-validation evidence.

## Exclusions

This workunit does not yet:
- read REGIS model values;
- interpret local confining conditions;
- map screens to hydrogeological units;
- infer absence of a confining unit from missing data;
- define a universal vertical-gradient threshold;
- change Stage-B evidence weights;
- assign `ADMISSIBLE_FREATIC`.

## Current status

`PHASE_1_IMPLEMENTED / LIVE_DISCOVERY_NOT_YET_QUALIFIED`

## Next permitted action

Run ordinary CI on the Phase-1 implementation. If green, trigger the live OPeNDAP metadata probe exactly once through the PR `ready_for_review` transition, inspect the compact artifact, and persist a resumable Phase-1 checkpoint before any point values are requested.
