# Stage-B GeoTOP 1.6.1 codebook authority — Gate 3E checkpoint

Status: **QUALIFIED_NETCDF_PAGE_DISCOVERY_GATE_3E**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_NETCDF_AUTHORITY_DISCOVERY`

## Repository state

- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- branch: `work/stage-b-geotop-codebook-authority`
- PR: #14
- qualified Gate-3E head: `051f3d818c12389ae4f59eab4605e040ea5d7b7d`
- tracking issue: #4

## Reused evidence

Gate 3E followed only the official child URL qualified by Gate 3D:

`https://www.dinoloket.nl/modelbestanden-aanvragen/netcdf`

No form/action/data request was invoked.

## Qualification

- ordinary CI run `35211528619`: PASS;
- live Gate-3E run `35211528568`: PASS;
- page SHA-256: `14cfa74e1675d4ee19f20b803b3427bab6ef118ef9e80cfbb6b6c95d08fbb8fb`;
- artifact ID: `10492310914`;
- artifact ZIP SHA-256: `0c1ac5dce789cb499d8c83815399cfcdaffe061b72bfa057e1ca8d75e4619c25`.

## Qualified live result

The page contains GeoTOP, NetCDF, download and OPeNDAP terminology, but:

- exposes no HTML forms;
- exposes no current reference-list file;
- exposes no direct current GeoTOP `.nc`, `.zip`, `.csv`, `.xlsx`, `.json` or `.xml` authority resource in the bounded inventory.

The only documentary child resource that could look relevant to format semantics is explicitly historical:

`GeoTOP v01r5 en NetCDF.pdf`

Because this resource is explicitly GeoTOP v1.5, it is not admissible as an exact GeoTOP 1.6.1 codebook without separate explicit compatibility evidence.

## Scientific boundary

The official public source chain followed in Gates 1, 2, 3C, 3D and 3E has therefore not produced an exact/current `REF_GTP_LITHO_CLASS` or `REF_GTP_STR_UNIT` delivery for GeoTOP 1.6.1.

This does not prove such reference lists do not exist. It proves only that they were not exposed through the bounded public authority route qualified here.

No meaning is assigned by this gate to:

- `lithok=0`;
- `strat=1000,3030,3100,4100,5000,5120`;
- or any other code based on historical-version inference.

## Verdict

**QUALIFIED_NETCDF_PAGE_DISCOVERY_GATE_3E**

The public current-delivery discovery route is exhausted for the present workunit without establishing a complete version-compatible codebook.

## Next permitted action

Close the authority decision surface against its predeclared qualification rule. The final authority verdict must distinguish explicit official semantic information from semantic mappings that are actually admissible for the exact GeoTOP 1.6.1 dataset. Historical/version-ambiguous mappings may be recorded as supporting evidence but must remain non-operative.
