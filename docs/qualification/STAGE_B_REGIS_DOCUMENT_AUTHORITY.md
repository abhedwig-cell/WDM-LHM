# Stage-B REGIS documentation authority

## Purpose
Extract and inspect exactly one formal documentation file from the already qualified REGIS II v2.2.3 archive chain before assigning semantics to raster filenames or values.

Authority member:
`REGIS II_v02r2s3/Toelichting op de bestanden van REGIS II v2.2.3.pdf`

## Dependency checkpoint
This workunit depends on the admitted recursive inventory in `STAGE_B_REGIS_RECURSIVE_INVENTORY.md` and therefore pins:
- source `brohgm.zip` SHA-256 `1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e`;
- `Model_HGM000000000062.zip` SHA-256 `ad852235b6ae512f8592c7f59126a7d238bb22580c9ce800cd61de1da7919645`;
- `REGIS II_v02r2s3.zip` SHA-256 `c983b244d9fa85478fcb7c3df4900b94e8a0282ac1b238b8081ed0f4bc785ea5`.

The inventory also established for the authority PDF:
- declared uncompressed size `900620` bytes;
- CRC32 `0bb0995f`.

Any mismatch fails closed.

## Scientific boundary
This workunit may:
- materialise the two known nested ZIP containers temporarily;
- extract exactly the authority PDF;
- hash, validate and read that PDF;
- record formal meanings explicitly stated by the document.

It may not:
- extract or open `.img` rasters;
- read raster values;
- use shapefile/XLSX/XML data as hydrogeological evidence;
- infer local confining conditions for monitoring wells;
- assign `ADMISSIBLE_FREATIC`;
- change Stage-B evidence weights.

## Qualification gates
1. Synthetic nested-ZIP tests prove exact-member extraction and hash-drift rejection.
2. Ordinary CI passes before live acquisition.
3. Live extraction is triggered once through `ready_for_review`.
4. The live source and both nested archives match the admitted hashes.
5. Exactly one non-ZIP member is extracted and it matches the admitted size/CRC.
6. The extracted file has a PDF header and is retained only as compact evidence.
7. The large source and nested ZIPs are removed before artifact upload.
8. The PDF is rendered/read separately and its semantic findings are persisted in a later checkpoint commit.

## Current status
`PLANNED / NOT YET LIVE-QUALIFIED`

No suffix or raster semantics are admitted by this document yet.
