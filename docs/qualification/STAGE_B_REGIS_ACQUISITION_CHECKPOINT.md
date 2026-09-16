# Stage-B REGIS acquisition checkpoint

Status: **QUALIFIED_ACQUISITION_METADATA**

Date: 2026-09-16

Branch under review: `work/stage-b-hydrogeological-admission`

## Capability

This workunit qualifies a reproducible and bounded acquisition path for BRO REGIS II evidence without yet interpreting hydrogeology or changing Stage-B freatic admission semantics.

Qualified components:

1. recursive public PDOK REGIS ATOM metadata discovery;
2. archive-candidate identification and HTTP HEAD provenance;
3. remote ZIP central-directory indexing through HTTP Range requests;
4. bounded extraction of explicit small archive members through HTTP Range requests;
5. size, CRC and compression-method validation;
6. fail-closed refusal of unbounded members, non-range fallback and unsupported ZIP variants.

## Scientific boundary

This checkpoint does **not** admit:

- automatic `ADMISSIBLE_FREATIC` decisions;
- interpretation of REGIS units at monitoring wells;
- a universal vertical-gradient threshold;
- treating REGIS as exact point-scale geology;
- a full REGIS model download in ordinary CI;
- use of REGIS as independent evidence without retaining model version and spatial support.

REGIS remains regional supporting evidence with approximately 100 x 100 m model support.

## Tests

GitHub Actions CI on Python 3.10 and 3.12: **PASS**.

Qualification suite on the acquisition head: **29/29 tests PASS**.

New tests cover:

- bounded ATOM recursion;
- no archive GET during metadata probing;
- remote ZIP EOCD / central-directory parsing;
- refusal when a server ignores Range requests;
- bounded DEFLATE member extraction;
- CRC and uncompressed-size checking;
- refusal of members beyond the configured extraction bound.

## Live PDOK evidence

### ATOM probe

Qualified live probe run: `35110896997` (initial metadata probe) and later repeated on the acquisition branch.

Public entry point:

`https://service.pdok.nl/tno/bro-regis-ii/atom/index.xml`

Discovered nested delivery feed:

`https://service.pdok.nl/tno/bro-regis-ii/atom/bro_regis_hydrogeologisch_model.xml`

Discovered archive:

`https://service.pdok.nl/tno/bro-regis-ii/atom/downloads/brohgm.zip`

Archive HEAD evidence:

- Content-Length: **1,180,207,038 bytes** (~1.10 GiB);
- media type: `application/zip`;
- Last-Modified: `Tue, 24 Mar 2026 10:46:38 GMT`;
- ETag: `0x8DE8992A0B37BF8`.

This size is intentionally not downloaded on every CI run.

### Remote ZIP range index

Qualified live range-index run: `35111359627`.

Outer archive EOCD / central-directory evidence:

- total entries: **3**;
- central-directory size: **219 bytes**;
- central-directory offset: `1,180,206,797`;
- outer object size: `1,180,207,038` bytes.

Outer archive members:

1. `MetaData_HGM000000000062.xml`
   - compression method: DEFLATE;
   - compressed: 12,530 bytes;
   - uncompressed: 50,151 bytes.
2. `MetaData_HGM000000000062.pdf`
   - compression method: DEFLATE;
   - compressed: 25,587 bytes;
   - uncompressed: 29,629 bytes.
3. `Model_HGM000000000062.zip`
   - compression method: DEFLATE;
   - compressed: 1,180,168,461 bytes;
   - uncompressed: 1,179,873,303 bytes.

The inner model ZIP is itself compressed as one outer ZIP member. Its own central directory is therefore not remotely seekable through the outer archive without processing the complete compressed member.

### Bounded metadata extraction

Qualified live workflow run: `35111751811`.

`MetaData_HGM000000000062.xml` was extracted by HTTP ranges only and validated by member size and CRC. No model archive content was downloaded.

The XML confirms at least:

- BRO ID: `HGM000000000062`;
- quality regime: `IMBRO`;
- registration/provenance metadata;
- generated-on timestamp `2026-03-24T11:43:58+01:00`;
- feedback / known-issue records for REGIS model units.

The metadata XML does **not** provide a file inventory of the inner `Model_HGM000000000062.zip` sufficient for targeted raster acquisition.

## Efficiency verdict

Repeated full REGIS downloads in ordinary CI are rejected as unnecessary and inefficient.

The qualified acquisition architecture is:

```text
ATOM metadata
  -> archive identity / version / ETag
  -> outer ZIP range index
  -> bounded small metadata extraction
  -> explicit decision whether a one-time full model inventory is necessary
```

## Next permitted action

Run a separate, explicit **one-time full inventory workunit** on a GitHub-hosted runner:

1. verify archive identity against this checkpoint (URL, size, ETag);
2. download the outer REGIS archive once;
3. extract only `Model_HGM000000000062.zip` locally on the runner;
4. list the inner ZIP central directory without extracting all model files;
5. persist only a compact inventory manifest with names, sizes, CRCs and relevant metadata;
6. delete the large temporary archives at job end;
7. do **not** upload the 1.18 GiB model as a GitHub artifact.

Only after that inventory is known may a separate workunit design selective model-file acquisition and hydrogeological column extraction for the Wageningen pilot.
