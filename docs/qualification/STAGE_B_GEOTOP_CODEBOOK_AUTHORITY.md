# Stage-B GeoTOP 1.6.1 codebook authority checkpoint

Status: **DESIGN_ONLY_AUTHORITY_CHECK_PENDING**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY`

This is a separate scientific decision surface following the merged GeoTOP acquisition/parser workunit in PR #13.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- source workunit verdict: `QUALIFIED_GEOTOP_ACQUISITION_AND_STRUCTURAL_PARSE_CODES_UNINTERPRETED`
- branch: `work/stage-b-geotop-codebook-authority`
- tracking issue: #4

## Reused immutable evidence

The preceding workunit qualified one GeoTOP column for `GMW000000020774_T1` and structurally parsed, without interpretation, these non-missing codes:

- `strat`: `1000, 3030, 3100, 4100, 5000, 5120`
- `lithok`: `0, 1, 2, 3, 5, 6, 7`

Qualified dataset metadata identifies:

- dataset endpoint: `https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc`
- `strat` long name: `lithostrat`
- `lithok` long name: `meest waarschijnlijke lithoklasse`
- `strat` missing token: `0`
- `lithok` missing token: `-127`

The qualified DDS/DAS metadata does not provide a semantic class-code dictionary.

## Scientific question

Does an explicit official TNO/DINOloket authority exist that is demonstrably version-compatible with GeoTOP 1.6.1 and maps the observed `strat` and/or `lithok` integer codes to geological class meanings?

## Authority hierarchy

A code translation may be admitted only from an explicit source that can be tied to the same GeoTOP dataset/version or to an official stable code list whose applicability to GeoTOP 1.6.1 is stated unambiguously.

Preferred evidence order:

1. code lists embedded in the exact GeoTOP 1.6.1 delivery or exact-dataset metadata;
2. official GeoTOP 1.6.1 documentation or model description from TNO/DINOloket;
3. an official TNO/DINOloket code-list publication explicitly declaring applicability to GeoTOP 1.6.1.

Search-engine snippets, third-party explanations, historical GeoTOP versions, inferred code-name conventions and integer magnitude are not authority.

## Qualification rule

The authority check must distinguish:

- `VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED`
- `PARTIAL_OR_AMBIGUOUS_AUTHORITY`
- `NO_VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED`

A positive result requires all of the following:

1. official source ownership is demonstrable;
2. source identity and content are persisted with URL and SHA-256;
3. version/applicability to GeoTOP 1.6.1 is explicit rather than inferred;
4. the relevant variable (`strat` or `lithok`) is identified explicitly;
5. each translated observed code is stated explicitly by the authority;
6. missing-value semantics remain those already qualified from the live dataset metadata.

Partial coverage remains partial. Unknown codes remain unknown.

## Exclusions

This workunit must not:

- reinterpret the raw GeoTOP column itself;
- correlate codes to q95 or the monitoring screen;
- infer permeability, aquitard behaviour or hydraulic continuity;
- substitute a code list from another GeoTOP version without explicit compatibility evidence;
- infer meanings from code prefixes or numerical order;
- turn absent documentation into evidence of geological absence;
- alter the Stage-B adjudication model;
- assign `ADMISSIBLE_FREATIC`;
- expand to other GMWs.

## Execution design

The authority acquisition must be bounded and provenance-first.

1. Inspect only official TNO/DINOloket resources already referenced by the exact GeoTOP dataset/service or an explicit official GeoTOP 1.6.1 documentation endpoint.
2. Persist raw authority material before semantic extraction.
3. Hash every retained authority file.
4. Extract only codebook/version/applicability evidence.
5. Fail closed when no explicit version-compatible mapping can be demonstrated.

Do not perform a broad internet or repository search merely to find a convenient mapping.

## Current verdict

**DESIGN_ONLY_AUTHORITY_CHECK_PENDING**

No code meaning is admitted by this document.

## Next permitted action

Implement a bounded official-source authority probe. Its first task is source discovery/identity only. Semantic code translation is not permitted until a source is acquired and version compatibility is independently qualified.