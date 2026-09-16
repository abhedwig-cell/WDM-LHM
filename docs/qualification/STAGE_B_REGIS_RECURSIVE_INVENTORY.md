# Stage-B REGIS recursive archive inventory

## Purpose
Reveal the complete nested archive structure of the current public REGIS II delivery until the first non-ZIP model files are visible, without extracting any non-ZIP model member.

This workunit follows `STAGE_B_REGIS_FULL_INVENTORY_CHECKPOINT.md`, which showed that `Model_HGM000000000062.zip` is itself a release wrapper containing another large archive, `REGIS II_v02r2s3.zip`.

## Scientific boundary
This capability is inventory only. It does not:
- read raster/grid values;
- assign hydrogeological units to monitoring wells;
- infer confining layers at point scale;
- produce `ADMISSIBLE_FREATIC`;
- modify Stage-B evidence weights.

## Execution model
The public `brohgm.zip` is downloaded once to an ephemeral GitHub runner. The recursive inventory then:
1. reads the central directory of the current archive;
2. records metadata for every member;
3. materialises only members whose filenames end in `.zip`;
4. recursively inventories those ZIP containers;
5. never opens/extracts non-ZIP members;
6. removes each materialised nested ZIP after its descendants are inventoried;
7. persists only compact CSV/JSON evidence.

## Fail-closed limits
- maximum archive recursion depth;
- maximum number of archive containers;
- maximum cumulative uncompressed bytes of materialised nested ZIP containers;
- any ZIP-named member must validate as an actual ZIP;
- member copy must consume the declared uncompressed byte count and complete CRC validation;
- any depth-limited ZIP member makes the live qualification incomplete;
- evidence upload is blocked if any output file exceeds 50 MB.

## Run-once workflow discipline
The heavy workflow is **not** triggered by ordinary PR synchronization. It runs on `pull_request: ready_for_review` (and explicit `workflow_dispatch`). The protocol used for this workunit was:
1. open the PR as draft;
2. let ordinary CI qualify the code and synthetic tests;
3. mark the PR ready only after CI is green;
4. run the heavy recursive inventory once;
5. persist this checkpoint in a later commit without rerunning the heavy job.

## Qualified live execution
Workflow run: `35118096882`

Qualified source:
- `brohgm.zip`
- size: `1,180,207,038` bytes
- SHA-256: `1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e`

Archive chain:

| depth | archive | size bytes | SHA-256 | members | ZIP children | non-ZIP files |
|---:|---|---:|---|---:|---:|---:|
| 0 | `brohgm.zip` | 1,180,207,038 | `1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e` | 3 | 1 | 2 |
| 1 | `Model_HGM000000000062.zip` | 1,179,873,303 | `ad852235b6ae512f8592c7f59126a7d238bb22580c9ce800cd61de1da7919645` | 9 | 1 | 8 |
| 2 | `REGIS II_v02r2s3.zip` | 1,144,397,416 | `c983b244d9fa85478fcb7c3df4900b94e8a0282ac1b238b8081ed0f4bc785ea5` | 5,004 | 0 | 4,999 |

The terminal archive is therefore conclusively `REGIS II_v02r2s3.zip`; no further ZIP wrapper exists.

Inventory totals:
- archive containers: `3`;
- maximum archive depth reached: `2`;
- depth-limited ZIP members: `0`;
- ZIP members materialised: `2`;
- cumulative materialised nested-ZIP bytes: `2,324,270,719`;
- total inventory entries over all archive levels: `5,016`;
- terminal non-ZIP model/delivery files at depth 2: `4,999`.

Terminal delivery file types include:

| extension | count |
|---|---:|
| `.img` | 954 |
| `.xml` | 2,229 |
| `.shp` | 330 |
| `.dbf` | 330 |
| `.shx` | 330 |
| `.prj` | 325 |
| `.cpg` | 298 |
| `.sbn` | 95 |
| `.sbx` | 95 |
| `.xlsx` | 11 |
| `.pdf` | 10 |
| `.lyr` | 1 |
| `.mxd` | 1 |

The scientific rasters in this delivery are principally Esri `.img` files; no GeoTIFF or ASCII-grid files were observed in the terminal archive inventory.

Observed raster filenames include examples such as `CKAKc-t-c.img`, `CKAKc-b-c.img`, `CKAKc-d-c.img`, `CKAKc-kh-s.img`, `CKAKc-kv-s.img`, `CKAKc-c.img`, `CKAKc-kd-verz.img`, `CKAKc-t-ql.img`, and `freatisch.img`. These names are **not yet interpreted** by this workunit.

A formal delivery document is present at:
`REGIS II_v02r2s3/Toelichting op de bestanden van REGIS II v2.2.3.pdf`

This is the preferred authority for interpreting the raster suffixes and delivery semantics before any raster values are read.

## Runtime evidence and guardrails
The live run reported:
- `nonzip_members_extracted = 0`;
- `interpretation_performed = false`;
- `admission_decision_performed = false`;
- `large_nested_archives_retained = false`;
- source ZIP removed before artifact upload.

Compact evidence artifact:
- workflow artifact ID: `10456373264`;
- artifact size: `87,837` bytes;
- artifact SHA-256: `40219ad5e5a64d651eed3d794ce213848ee462856e1917029032958f7dfd7d10`;
- contents: recursive inventory CSV, container CSV, manifest, source headers and runner disk evidence only.

The resumable download capability was available but was not exercised by a disconnect in this successful run: the source completed on the first outer attempt.

## Verdict
**PASS — recursive archive discovery qualified.**

This verdict means the archive structure and terminal delivery file inventory are admitted as evidence. It does **not** admit any hydrogeological interpretation of the `.img` rasters and does **not** change monitoring-well freatic status.

## Next permitted action
Create a separate documentation-only workunit that extracts and reads only `Toelichting op de bestanden van REGIS II v2.2.3.pdf` from the proven archive chain, records its provenance/hash, and derives the formal meaning of REGIS raster/file suffixes from that source.

Only after those semantics are documented may a targeted raster metadata/value extraction for the Wageningen pilot be designed.
