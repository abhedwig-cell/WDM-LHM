# Stage-B GeoTOP 1.6.1 codebook authority — final disposition

Status: **PARTIAL_OR_AMBIGUOUS_AUTHORITY**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY`

## Decision question

Can an explicit official authority be established that is demonstrably applicable to the exact GeoTOP 1.6.1 delivery and maps the observed `strat` and `lithok` integer codes used by the qualified column for `GMW000000020774_T1`?

## Predeclared positive rule

A semantic mapping is admissible only when all of the following are satisfied:

1. official source ownership is demonstrable;
2. source identity/content is persisted with URL and SHA-256;
3. applicability to GeoTOP 1.6.1 is explicit rather than inferred;
4. the relevant variable is explicitly identified;
5. each translated observed code is explicitly stated by that authority;
6. the already-qualified missing-value semantics are preserved.

Unknown and partial coverage remain unknown/partial.

## Exact dataset evidence

The qualified live GeoTOP service identifies:

- dataset: GeoTOP 1.6.1;
- institution: TNO / Geologische Dienst Nederland;
- `strat`: `lithostrat`, missing token `0`;
- `lithok`: `meest waarschijnlijke lithoklasse`, missing token `-127`.

The observed non-missing column values remain:

- `strat`: `1000, 3030, 3100, 4100, 5000, 5120`;
- `lithok`: `0, 1, 2, 3, 5, 6, 7`.

The exact dataset metadata does not enumerate semantic mappings for these codes.

## Official semantic evidence found

### General GeoTOP report

The exact-hash official general GeoTOP report acquired in Gate 3A contains an explicit GeoTOP lithoklasse table and describes the official reference lists `REF_GTP_LITHO_CLASS` and `REF_GTP_STR_UNIT`.

That report explicitly documents meanings for the observed lithoklasse numbers:

- `1`: organic/peat material;
- `2`: clay;
- `3`: clayey sand / sandy clay / loam grouping;
- `5`: fine sand;
- `6`: medium sand;
- `7`: coarse sand.

It does not establish a meaning for observed `lithok=0` in the exact 1.6.1 dataset, and it does not explicitly map the observed `strat` values `1000, 3030, 3100, 4100, 5000, 5120`.

### Version-chain evidence

The exact-hash GeoTOP v1.6 supplement documents changes relative to earlier releases, including changes to the geological-unit reference list. It does not provide an explicit statement that the complete lithoklasse reference list from the general report is the exact reference list applicable to GeoTOP v1.6.

The exact-hash GeoTOP v1.6.1 small-release memo visibly states on page 1 that, relative to GeoTOP v1.6, only the geological-unit model-uncertainty attribute was changed and the other attributes remained unchanged. This is strong evidence for continuity from v1.6 to v1.6.1, but it does not by itself establish the missing explicit bridge between the older/general reference-list authority and v1.6.

Therefore the required version/applicability condition cannot be completed without inference.

## Bounded current-delivery discovery

The public authority chain was followed without generic search:

1. exact GeoTOP 1.6.1 service metadata;
2. dataset `references` page;
3. current `bekijken-en-aanvragen-geotop` page;
4. `modelbestanden-aanvragen` page;
5. `modelbestanden-aanvragen/netcdf` page.

This chain did not expose an exact/current downloadable `REF_GTP_LITHO_CLASS` or `REF_GTP_STR_UNIT` for GeoTOP 1.6.1.

The NetCDF page exposes a documentary link explicitly labelled for GeoTOP v1.5. That historical resource is not substituted for 1.6.1 authority.

Absence from this bounded public chain is not evidence that the reference lists do not exist. It is only evidence that this workunit did not establish them through the qualified public route.

## Formal verdict

**PARTIAL_OR_AMBIGUOUS_AUTHORITY**

Rationale:

- official semantic information exists;
- the semantic information is incomplete for the observed codes;
- exact GeoTOP 1.6.1 applicability of the older/general reference-list semantics is not explicit enough to satisfy the predeclared positive rule;
- a current-delivery codebook was not exposed through the bounded official public route.

This is not `VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED`.

It is also not `NO_VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED` in the stronger sense of demonstrating non-existence, because the bounded route cannot prove that an exact current reference list is unavailable elsewhere in the official delivery process.

## Operational disposition

For Stage-B adjudication:

- `version_compatible_codebook_established = false`;
- admitted `lithok` semantic mappings: **none**;
- admitted `strat` semantic mappings: **none**;
- `lithok=0` remains unknown;
- all observed `strat` meanings remain unknown;
- historical/general lithoklasse meanings may be retained only as non-operative supporting evidence;
- no code prefix, number magnitude or historical version may be used to fill gaps;
- no GeoTOP class meaning may be used to establish hydraulic continuity or positive freatic admission.

The existing missing-value semantics remain unchanged:

- `strat=0` is missing for the qualified dataset;
- `lithok=-127` is missing for the qualified dataset;
- unknown semantic meaning is not converted to missing and is not converted to `no`.

## Consequence for GMW000000020774_T1

GeoTOP remains contextual regional evidence only. This authority workunit does not provide the missing positive local hydraulic-continuity evidence required for `ADMISSIBLE_FREATIC`.

The candidate therefore remains fail-closed. No positive Stage-B admission is authorized by this workunit.

## Exclusions retained

This disposition does not:

- alter the Stage-B adjudication algorithm;
- implement a score or threshold;
- infer hydraulic behaviour from lithology;
- correlate GeoTOP classes to the q95/screen interval as a positive admission rule;
- recalibrate LHM;
- expand to other GMWs.

## Next permitted action

The authority question may be reopened only with new explicit evidence, for example:

- an exact GeoTOP 1.6.1 delivery containing `REF_GTP_LITHO_CLASS` / `REF_GTP_STR_UNIT`;
- an official current TNO/DINOloket code list explicitly declaring applicability to GeoTOP 1.6.1;
- or an explicit TNO/GDN statement establishing the version compatibility of the relevant reference lists.

Absent such evidence, do not continue public-source chasing merely to force semantic classification. Return to the Stage-B adjudication evidence hierarchy and treat GeoTOP semantics as insufficient for positive admission of `GMW000000020774_T1`.
