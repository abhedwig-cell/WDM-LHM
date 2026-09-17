# Stage-B GeoTOP 20774 acquisition checkpoint

Status: **DESIGN_GEOTOP_METADATA_PROBE_PENDING_LIVE**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_20774_ACQUISITION`

This workunit follows the qualified `NO_LOCAL_BHRG_FOUND` boundary from PR #12. It acquires bounded GeoTOP evidence for `GMW000000020774` only. Acquisition and interpretation remain separate.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start: `1d09affe80c0b9d305d0d1be6d366b9b02a02107`
- branch: `work/stage-b-geotop-20774-acquisition`
- parent verdict: `QUALIFIED_LOCAL_BHRG_ACQUISITION_NO_LOCAL_OBJECTS`
- tracking surface: issue #4

## Reused immutable target evidence

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m`
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW, BRO, REGIS or GeoTOP rediscovery is permitted in this workunit.

## GeoTOP authority and scale boundary

The current public model authority is BRO GeoTOP v1.6.1 (2025), published by TNO Geological Survey of the Netherlands. GeoTOP is a subregional model intended for provincial, municipal and district-scale use; at well scale it is supporting context rather than local truth.

The public OPeNDAP dataset is:

`https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc`

The voxel model is expected to expose a 100 m horizontal grid and 0.5 m vertical voxels, but this workunit does not trust those dimensions from prose alone. The live metadata probe must establish the exact dataset descriptor and attributes before any index or data extraction is implemented.

## Gate 1: metadata-only probe

The first live gate may only retrieve and persist:

- OPeNDAP DDS;
- OPeNDAP DAS;
- endpoint/provenance metadata;
- SHA-256 and byte counts;
- a compact machine-readable inventory of declared dimensions and variable names parsed from DDS/DAS.

It must not request any voxel values.

The gate must fail closed if:

- the host/path drifts away from the fixed GeoTOP dataset;
- DDS or DAS cannot be retrieved;
- the response is empty or not parseable as the expected OPeNDAP text metadata;
- required coordinate dimensions/variables cannot be established;
- duplicate or internally inconsistent dimension declarations are found.

## Gate 2: bounded point-column acquisition

Gate 2 is not permitted until Gate 1 is qualified.

After exact dimensions, coordinate semantics and variable names are known, a separate atomic commit may:

1. determine the nominal GeoTOP cell containing the fixed RD target using the live coordinate arrays/metadata;
2. record horizontal boundary distance and preserve neighbour sensitivity if the coordinate is close to a cell edge;
3. request exactly one vertical column, plus explicitly justified neighbour columns only when required by boundary sensitivity;
4. retain raw OPeNDAP responses and hashes;
5. emit typed raw values without mapping them to hydraulic meaning.

No spatial averaging is permitted.

## Scientific exclusions

This workunit must not:

- convert lithological class to hydraulic conductivity;
- infer a confining layer from a categorical voxel code alone;
- infer hydraulic continuity from GeoTOP alone;
- replace BRO ground level with a GeoTOP surface elevation;
- use REGIS `freatisch` or `kD`;
- change the Stage-B decision model;
- assign `ADMISSIBLE_FREATIC`;
- enable `allow_admissible=True`.

Missing or unknown remains missing or unknown.

## Qualification plan

Gate 1 synthetic tests must cover:

- fixed endpoint construction;
- DDS dimension parsing;
- variable inventory parsing;
- malformed/empty metadata rejection;
- duplicate/inconsistent dimension rejection;
- proof that no data constraint expression is issued in metadata-only mode.

Gate 1 live qualification must run on the same PR head as ordinary CI and persist immutable metadata artifacts.

## Verdict

**DESIGN_GEOTOP_METADATA_PROBE_PENDING_LIVE**

## Next permitted action

Implement and qualify Gate 1 only. Do not implement point-column indexing or lithological interpretation until the live GeoTOP DDS/DAS contract is pinned.