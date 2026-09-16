# REGIS full-inventory workunit

## Purpose

This workunit is the explicitly permitted next step after `STAGE_B_REGIS_ACQUISITION_CHECKPOINT.md`.

The public REGIS II delivery contains a ~1.18 GB nested `Model_HGM000000000062.zip` member. Because that member is itself DEFLATE-compressed inside the outer delivery ZIP, its central directory cannot be reached by HTTP Range requests without first processing the complete nested member.

This workunit therefore performs a **one-time ephemeral full acquisition** whose only admitted output is a compact inventory of the nested model ZIP.

## Allowed operations

1. download the current public `brohgm.zip` to ephemeral GitHub runner storage;
2. verify that the object is a ZIP and has an expected bounded size;
3. stream-decompress `Model_HGM000000000062.zip` to temporary local runner storage;
4. validate the nested ZIP CRCs;
5. read the nested ZIP central directory;
6. record filename, directory flag, extension, compressed/uncompressed size, compression method and CRC32 for every nested member;
7. hash the outer and inner ZIP bytes for provenance;
8. delete both large temporary ZIP files;
9. upload only the compact JSON/CSV inventory and small provenance logs.

## Explicit exclusions

This workunit must **not**:

- extract any REGIS model raster/grid member;
- interpret hydrogeological units;
- sample REGIS values at monitoring wells;
- decide whether a monitoring tube is freatic;
- upload the national model or nested model ZIP as a GitHub artifact;
- turn this one-time inventory into ordinary CI.

## Artifact guardrail

The workflow fails if any evidence file destined for artifact upload exceeds 50 MB. The two large archives must live only under ephemeral `/tmp` storage and be deleted before artifact upload.

## Admission target

A successful run qualifies only the statement:

> The internal file structure of the current REGIS II model delivery has been reproducibly inventoried without persisting or interpreting model data.

The resulting inventory may then be used to design the next, smaller workunit that acquires only the specific file(s) needed for hydrogeological evidence around the pilot monitoring wells.
