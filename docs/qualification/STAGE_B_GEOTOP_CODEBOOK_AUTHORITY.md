# Stage-B GeoTOP 1.6.1 codebook authority checkpoint

Status: **QUALIFIED_AUTHORITY_DOCUMENT_ACQUISITION_GATE_3A**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY`

This is a separate scientific decision surface following the merged GeoTOP acquisition/parser workunit in PR #13.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- source workunit verdict: `QUALIFIED_GEOTOP_ACQUISITION_AND_STRUCTURAL_PARSE_CODES_UNINTERPRETED`
- branch: `work/stage-b-geotop-codebook-authority`
- PR: #14
- Gate-1 implementation head: `2fe765fc93b4076bacb5a50abf700d3528e0641d`
- Gate-2 implementation head: `74f3a33e1a22c2c1fc3382dbaf214dc6267cfe05`
- Gate-3A implementation head: `9c21eeb4a43a9cb0efc5c4a1a1790383c275756f`
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

## Authority hierarchy and positive rule

A code translation may be admitted only from an explicit source tied to the same GeoTOP dataset/version or an official stable code list whose applicability to GeoTOP 1.6.1 is stated unambiguously.

Preferred evidence order:

1. code lists embedded in the exact GeoTOP 1.6.1 delivery or exact-dataset metadata;
2. official GeoTOP 1.6.1 documentation or model description from TNO/DINOloket;
3. an official TNO/DINOloket code-list publication explicitly declaring applicability to GeoTOP 1.6.1.

A positive result requires all of the following:

1. official source ownership is demonstrable;
2. source identity and content are persisted with URL and SHA-256;
3. version/applicability to GeoTOP 1.6.1 is explicit rather than inferred;
4. the relevant variable (`strat` or `lithok`) is identified explicitly;
5. each translated observed code is stated explicitly by the authority;
6. missing-value semantics remain those already qualified from the live dataset metadata.

The final authority verdict must be one of:

- `VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED`;
- `PARTIAL_OR_AMBIGUOUS_AUTHORITY`;
- `NO_VERSION_COMPATIBLE_CODEBOOK_ESTABLISHED`.

Partial coverage remains partial. Unknown codes remain unknown.

## Gate 1: exact dataset-service source discovery

Verdict: **QUALIFIED_OFFICIAL_SOURCE_DISCOVERY**

Gate 1 acquired only the exact dataset `.html` and `.info` service resources. Qualification on head `2fe765fc93b4076bacb5a50abf700d3528e0641d`:

- ordinary CI run `35201211479`: PASS;
- live authority-discovery run `35201211658`: PASS;
- artifact `10488331168`, ZIP SHA-256 `4997b1a5b74f9a7a90223b60bd2f1ae7e5faf26ffea0626b491a0d91f8d962be`;
- service HTML SHA-256 `9fd0d3ee52abcf88e7299d995899cbc5ec8f465ea6ac62b1cb743ff22d063cec`;
- service INFO SHA-256 `58ba6534d1f01a3fb97c790260f37748f404ac2acef249db5de6f97f73b0eac1`.

The exact service resources explicitly identify `GeoTOP 1.6.1 (lithoklasse)`, TNO / Geologische Dienst Nederland, `strat` as `lithostrat`, and `lithok` as `meest waarschijnlijke lithoklasse`. They do not enumerate semantic code mappings.

The dataset global `references` attribute points to:

`http://www.dinoloket.nl/detaillering-van-de-bovenste-lagen-met-geotop`

No class-code meaning was admitted in Gate 1.

## Gate 2: dataset-referenced official page

Verdict: **QUALIFIED_DATASET_REFERENCE_PAGE**

Gate 2 acquired only the exact page named by the dataset `references` attribute, following its official redirect to:

`https://www.dinoloket.nl/detaillering-van-de-bovenste-lagen-met-geotop`

Qualification on head `74f3a33e1a22c2c1fc3382dbaf214dc6267cfe05`:

- ordinary CI run `35201518277`: PASS;
- Python 3.10 and 3.12 both PASS, `143 passed` on Python 3.12;
- Gate-1 recheck run `35201518279`: PASS;
- live Gate-2 run `35201518681`: PASS;
- page SHA-256 `492561fe51e5cda63f7b37cfe61a961d03fce785f67d817194b99ea1512542e1`;
- artifact `10488133062`, ZIP SHA-256 `ad6cdf678f6598b256f42e314ad30b9d196ec08309c26a3c96e4ca7d4b16ded1`.

The page explicitly contains GeoTOP/version/code terminology and links official documentation including:

- `R11636 Totstandkomingsrapport GeoTOP - aanvullingen bij versie v1.6.pdf`;
- `Toelichting bij kleine release GeoTOP v1.6.1 - Modelonzekerheid van geologische eenheid.pdf`;
- `R11655 Totstandkomingsrapport GeoTOP.pdf`;
- additional older/release-specific material not selected for the next bounded gate.

Gate 2 inventories links only. It does not establish that any linked document contains a usable codebook and does not translate codes.

## Gate 3A: bounded official authority-document acquisition

Verdict: **QUALIFIED_AUTHORITY_DOCUMENT_ACQUISITION**

Exactly three official PDFs named by the qualified Gate-2 page were acquired, raw bytes first, before analysis:

1. `v16_supplement`
   - final URL: `https://www.dinoloket.nl/sites/default/files/2023-10/R11636%20Totstandkomingsrapport%20GeoTOP%20-%20aanvullingen%20bij%20versie%20v1.6.pdf`
   - bytes: `1192495`
   - SHA-256: `d35108ce0749007935565778392dd4d4d32a40ad08d48f6c5c37d833b0746ad3`
2. `v161_small_release`
   - final URL: `https://www.dinoloket.nl/sites/default/files/2025-03/Toelichting%20bij%20kleine%20release%20GeoTOP%20v1.6.1%20-%20Modelonzekerheid%20van%20geologische%20eenheid.pdf`
   - bytes: `2723550`
   - SHA-256: `9b50b3a2d1b02d3292ef4f5259a6716f1f0aa0ae11341ad5b0eb9c80a4a5ba83`
3. `general_report`
   - final URL: `https://www.dinoloket.nl/sites/default/files/docs/geotop/R11655%20Totstandkomingsrapport%20GeoTOP.pdf`
   - bytes: `10341950`
   - SHA-256: `9c72f77d4ec84272ec007e7c31e8f60877aec10d5abf1d77fd9b0cdb11bf3cba`

Qualification on exact head `9c21eeb4a43a9cb0efc5c4a1a1790383c275756f`:

- ordinary CI run `35205087744`: PASS;
- Python 3.10: `148 passed`;
- Python 3.12: `148 passed`;
- Gate-1 recheck run `35205087727`: PASS;
- Gate-2 recheck run `35205087702`: PASS;
- Gate-3A live run `35205087766`: PASS;
- artifact ID `10489402091`;
- artifact ZIP SHA-256 `13ad33c6ef16fde6d83e5a31ff62a471d057925d6c7961466f850511a4e5a942`.

Guardrails proven by Gate 3A:

- fixed three-document set only;
- official DINOloket source only;
- raw PDF bytes persisted before analysis;
- no PDF text extraction;
- no code-table extraction;
- no code translation;
- no version-compatibility conclusion;
- no geological or hydraulic interpretation;
- no admission decision.

## Exclusions retained

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

## Current verdict

**QUALIFIED_AUTHORITY_DOCUMENT_ACQUISITION_GATE_3A**

No class-code meaning has been admitted.

## Next permitted action

Gate 3B may perform deterministic text extraction from only the three Gate-3A documents. Before extraction it must reacquire or consume the persisted documents and verify the exact qualified SHA-256 values above. The extraction must persist text plus provenance and may search only for the authority question: explicit GeoTOP version/applicability statements, explicit `strat`/`lithok` variable or class-list definitions, and explicit mappings for the already observed codes. It must not infer code meanings from context, prefixes, numeric order, figures or geological expectation. Semantic admission remains closed until the extracted evidence satisfies the positive rule above.