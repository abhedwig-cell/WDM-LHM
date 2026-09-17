# Stage-B GeoTOP 1.6.1 codebook authority — Gate 3D checkpoint

Status: **QUALIFIED_MODEL_FILES_PAGE_DISCOVERY_GATE_3D**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_MODEL_FILES_AUTHORITY_DISCOVERY`

## Repository state

- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- branch: `work/stage-b-geotop-codebook-authority`
- PR: #14
- qualified Gate-3D head: `2effd10fc378a5960c9a2d33eef2f8f9cdd2c209`
- tracking issue: #4

## Reused evidence

Gate 3D followed only the official URL qualified by Gate 3C:

`https://www.dinoloket.nl/modelbestanden-aanvragen`

The gate inventoried links and HTML form structure only. It submitted no form and invoked no action.

## Qualification

- ordinary CI run `35211288710`: PASS on Python 3.10 and 3.12;
- live Gate-3D run `35211288727`: PASS;
- page SHA-256: `39440852a41e84f3bce4a301fbf8aca3709f1d111315d172fecb7bf5c5a38fee`;
- artifact ID: `10492685102`;
- artifact ZIP SHA-256: `6c6ca3a0a3d11cd32882436b8bdd3258c32c77f1a187d87ff01ca8e443e24c71`.

## Qualified live result

The page contains GeoTOP/model-file/download/request terminology but:

- exposes no HTML forms in the acquired page;
- exposes no direct reference-list file;
- exposes no direct `.zip`, `.csv`, `.xlsx`, `.json` or `.xml` authority resource in the bounded link inventory.

The only new relevant official child path is:

`https://www.dinoloket.nl/modelbestanden-aanvragen/netcdf`

Self-links and fragments were also present and are not new evidence.

## Scientific boundary

No code semantics or version compatibility has been established. In particular:

- `lithok=0` remains unknown;
- observed `strat` codes remain unknown;
- no geological/hydraulic inference is made;
- no Stage-B adjudication outcome changes.

## Verdict

**QUALIFIED_MODEL_FILES_PAGE_DISCOVERY_GATE_3D**

The model-files landing page does not itself provide the current reference lists needed for semantic admission.

## Next permitted action

Gate 3E may acquire only `https://www.dinoloket.nl/modelbestanden-aanvragen/netcdf`, because it is the only new relevant official child path exposed by Gate 3D. It may inventory raw HTML, official links and form structure only. It must not submit requests, invoke actions, download newly discovered resources, translate codes or infer geology/hydraulics.
