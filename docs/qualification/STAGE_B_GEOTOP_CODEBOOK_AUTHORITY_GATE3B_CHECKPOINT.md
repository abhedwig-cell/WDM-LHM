# Stage-B GeoTOP 1.6.1 codebook authority — Gate 3B checkpoint

Status: **QUALIFIED_AUTHORITY_TEXT_EXTRACTION_GATE_3B**

Date: 2026-09-17

## Capability

`STAGE_B_GEOTOP_161_CODEBOOK_AUTHORITY_TEXT_EXTRACTION`

## Repository state

- repository: `abhedwig-cell/WDM-LHM`
- canonical `main`: `3cce6d69af54b213b07c03b85f9e61c800ef93fd`
- branch: `work/stage-b-geotop-codebook-authority`
- PR: #14
- qualified Gate-3B head: `4fa8b2ff150d555beb37eb0fcfa10acb402ccc13`
- tracking issue: #4

## Dependencies and reused evidence

Gate 3B consumes only the three Gate-3A official DINOloket PDFs and requires their exact previously qualified SHA-256 values before text extraction:

- `v16_supplement`: `d35108ce0749007935565778392dd4d4d32a40ad08d48f6c5c37d833b0746ad3`
- `v161_small_release`: `9b50b3a2d1b02d3292ef4f5259a6716f1f0aa0ae11341ad5b0eb9c80a4a5ba83`
- `general_report`: `9c72f77d4ec84272ec007e7c31e8f60877aec10d5abf1d77fd9b0cdb11bf3cba`

The source column remains the already qualified GeoTOP 1.6.1 column for `GMW000000020774_T1`, with observed, still uninterpreted codes:

- `strat`: `1000, 3030, 3100, 4100, 5000, 5120`
- `lithok`: `0, 1, 2, 3, 5, 6, 7`

## Qualification

Ordinary CI on exact head `4fa8b2ff150d555beb37eb0fcfa10acb402ccc13`:

- run `35210103570`: PASS;
- Python 3.10: PASS;
- Python 3.12: PASS, `152 passed`.

Live text-extraction qualification:

- run `35210103507`: PASS;
- extractor: `pdftotext version 24.02.0`;
- artifact ID: `10491711157`;
- artifact ZIP SHA-256: `4d02238733730f0672bfe477d9e4af825ecd84c0874fa49669e6a86e79f290fa`.

Extracted immutable text evidence:

1. `general_report`
   - pages: `132`
   - text bytes: `302307`
   - text SHA-256: `96d50afe051ecb11460a1f960a36fa0ee6ae3a6b2043d5ed3dafcf34f8676b2f`
2. `v16_supplement`
   - pages: `40`
   - text bytes: `93990`
   - text SHA-256: `1b6cd428821911d1af2c71052ef6a12b0a019ca0570738e1ae99a190459927ff`
3. `v161_small_release`
   - pages: `13`
   - extracted text bytes: `624`
   - text SHA-256: `5766210737315b3d1c65f2b414d024d652eb8f8b03a9da811d6842b245fdc4cb`
   - note: the PDF has a sparse/non-useful machine-readable text layer; this is an extraction limitation, not evidence that the document has no relevant visible content.

## Evidence boundary reached

The deterministic extraction establishes where authority signals occur but does not itself admit a code translation.

The exact-hash `general_report` contains an explicit official GeoTOP lithoklasse table and official reference-list descriptions. In particular, it provides explicit meanings for observed `lithok` values `1, 2, 3, 5, 6, 7`, and describes reference list `REF_GTP_LITHO_CLASS`. It also describes `REF_GTP_STR_UNIT` for geological-unit codes.

However:

- observed `lithok=0` is not yet assigned a meaning by qualified authority evidence;
- the observed `strat` values `1000, 3030, 3100, 4100, 5000, 5120` are not explicitly mapped by the currently qualified document text;
- historical/general GeoTOP documentation is not by itself sufficient to claim that every listed code mapping applies unchanged to the exact GeoTOP 1.6.1 delivery;
- the v1.6.1 PDF's visible page 1 states that only the geological-unit model-uncertainty attribute changed relative to v1.6 and other attributes remained unchanged, but this visible-page evidence has not yet been turned into an automated codebook admission and does not bridge the older general-report reference lists to the exact current delivery by itself.

Therefore the authority verdict remains open and fail-closed. No code meaning is yet wired into Stage-B adjudication.

## Guardrails retained

Gate 3B performed no:

- geological or hydraulic interpretation of the GMW column;
- inference from code prefixes or numeric order;
- mapping of unknown `lithok=0`;
- mapping of the observed `strat` values;
- q95/screen correlation;
- change to the Stage-B adjudication model;
- `ADMISSIBLE_FREATIC` decision;
- expansion to other GMWs.

## Verdict

**QUALIFIED_AUTHORITY_TEXT_EXTRACTION_GATE_3B**

This is an evidence-extraction qualification, not a semantic admission.

## Next permitted action

Gate 3C may follow only a qualified official link already present on the Gate-2 dataset-reference page, beginning with `https://www.dinoloket.nl/bekijken-en-aanvragen-geotop`, to determine whether the exact/current GeoTOP delivery exposes version-compatible reference lists or a data catalogue for `REF_GTP_LITHO_CLASS` and `REF_GTP_STR_UNIT`.

Gate 3C must:

- persist source URL, final URL, raw bytes and SHA-256 before interpretation;
- inventory only official DINOloket/TNO links;
- not perform generic web search;
- not infer semantics from filenames or code values;
- prefer an actual current reference list over historical-document inference;
- stop fail-closed if no explicit current-delivery authority is exposed.
