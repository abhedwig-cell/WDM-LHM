# Stage-B REGIS geometric screen-overlap checkpoint

Status: **QUALIFIED_GEOMETRY_ONLY_REAL_DATA**

Date: 2026-09-17

Branch under review: `work/regis-point-columns`

## Capability

This checkpoint qualifies exact vertical overlap between the two admitted TS07 multi-filter cases and three previously qualified REGIS v02r2s3 point columns.

The capability is deliberately geometry-only. It does not interpret REGIS layer codes hydraulically and it does not assign `ADMISSIBLE_FREATIC`.

## Dependencies

- qualified TS07 real-data checkpoint: `docs/qualification/TS07_CHECKPOINT.md`;
- qualified REGIS OPeNDAP dataset identity: `REGIS v02r2s3`, EPSG:28992;
- qualified grid mapping including the 4074 west-neighbour sensitivity column;
- qualified parsed hydro-column SHA-256: `155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8`;
- parsed variables used for geometry: `top` and `bottom` only. `kh`, `kv` and `c` remain uninterpreted here;
- `freatisch` and `kD` remain excluded as independent evidence against LHM.

BRO ground level is the authority for converting screen depths below ground level to screen elevations in m NAP. REGIS `mv` is retained only as a scale/position diagnostic and is never used to shift a screen.

## Synthetic qualification

Repository CI on head `719655010fd1885094ebf6e9c188019a536eac0f`: **PASS on Python 3.10 and 3.12**.

Targeted tests cover:
- exact BRO-based screen-elevation derivation;
- exact interval overlap;
- 4074 boundary-sensitivity preservation;
- REGIS `mv` diagnostic semantics;
- parsed-hash drift rejection;
- fail-closed rejection of overlapping/double-counted REGIS layer geometry.

## Live qualification

GitHub Actions workflow: `REGIS geometric screen overlap qualification`

Run: `35181574136` — **PASS**

Artifact:
- ID: `10480936971`;
- name: `regis-screen-overlap-35181574136`;
- artifact digest SHA-256: `a14fae5625735623da63ba37267ccd46b07a8534976875088f956559a2062391`;
- `regis_screen_overlap.json` SHA-256: `ef10948ac2b9d83566a52081f7f0c1e78e4dd7ac33b2c03c7c7884415f0dafc1`;
- output size: `8275` bytes.

The live workflow reacquired the three pinned point columns, reproduced the qualified parsed-hydro SHA-256, computed the overlaps, validated the expected real-data geometry and uploaded bounded evidence.

## Qualified screen geometry

### GMW000000004074 — Tube 1

BRO screen:
- ground level: `7.93 m NAP`;
- screen: `2.21–5.21 m below ground`;
- screen elevation: `5.72 to 2.72 m NAP`;
- length: `3.00 m`.

Nominal REGIS cell `(x=1703, y=1407)`:
- `NUBXz3`: `0.69 m`;
- `NUBXz4`: `1.07 m`;
- `NUgsc`: `1.24 m`.

West sensitivity cell `(x=1702, y=1407)`:
- `NUgsc`: `3.00 m`.

The layer sequence therefore changes materially across the cell boundary. The two columns are retained side-by-side and are never averaged.

### GMW000000004074 — Tube 2

BRO screen elevation: `-3.16 to -3.66 m NAP`, length `0.50 m`.

Both the nominal and west sensitivity columns place the complete screen interval in `NUgsc` (`0.50 m`).

### GMW000000004104 — Tube 1

BRO screen elevation: `-2.21 to -4.21 m NAP`, length `2.00 m`.

The nominal REGIS column places the complete interval in `NUgsc` (`2.00 m`).

### GMW000000004104 — Tube 2

BRO screen elevation: `-26.17 to -28.17 m NAP`, length `2.00 m`.

The nominal REGIS column places the complete interval in `NUPZ-WAz1` (`2.00 m`).

All four screen intervals are fully covered geometrically in the queried REGIS columns; no gap or imputation was introduced.

## REGIS surface diagnostic

REGIS `mv` is not used for screen elevations. It is reported only to expose regional/local support differences:

| column | REGIS mv (m NAP) | BRO ground (m NAP) | REGIS - BRO (m) |
|---|---:|---:|---:|
| 4074 nominal | 8.15 | 7.93 | +0.22 |
| 4074 west neighbour | 7.77 | 7.93 | -0.16 |
| 4104 nominal | 11.15 | 9.81 | +1.34 |

The `+1.34 m` discrepancy at 4104 is a material warning against treating regional REGIS surface geometry as local truth.

## Scientific interpretation boundary

This checkpoint admits the geometry, not the hydrogeological meaning of the layer codes.

The evidence does support two methodological conclusions:

1. `GMW000000004074` Tube 1 is too close to a REGIS cell boundary for a unique regional-model layer assignment to be treated as robust local evidence. Its nominal and west-neighbour assignments differ materially.
2. REGIS provides useful regional context, but the 100 m support and local `mv` discrepancies mean it must remain subordinate to direct BRO/GLD and same-GMW multi-filter evidence in Stage-B freatic adjudication.

No universal spatial tolerance is introduced. The 4074 neighbour column was added because this specific qualified point lies only about 5.6 mm from the x=170300 m cell boundary.

## Guardrails

The qualified artifact records:
- geometry only: `true`;
- BRO ground level is screen-elevation authority: `true`;
- REGIS `mv` diagnostic only: `true`;
- hydraulic-property interpretation performed: `false`;
- layer-code semantics applied: `false`;
- columns averaged: `false`;
- admission decision performed: `false`.

## Verdict

**PASS — real-data REGIS screen geometry is qualified for these two multi-filter cases.**

REGIS is admitted as supporting regional hydrogeological context, not as a local freatic-admission authority.

## Next permitted action

Move to a separate Stage-B adjudication decision surface that combines:
- empirical groundwater-fluctuation-zone position relative to each screen;
- same-GMW vertical-head evidence;
- the qualified REGIS geometry as supporting context;
- explicit uncertainty / review status when regional geometry is boundary-sensitive.

The adjudication must not create a universal vertical-head threshold, must not use `freatisch` as independent evidence against LHM, and must keep `GMW000000004074` Tube 1 fail-closed if the combined evidence remains ambiguous.
