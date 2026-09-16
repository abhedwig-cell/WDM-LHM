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
The heavy workflow is **not** triggered by ordinary PR synchronization. It runs on `pull_request: ready_for_review` (and explicit `workflow_dispatch`). The intended protocol is:
1. open the PR as draft;
2. let ordinary CI qualify the code and synthetic tests;
3. mark the PR ready only after CI is green;
4. run the heavy recursive inventory once;
5. persist a checkpoint in a later commit without rerunning the heavy job.

If the heavy run must be repeated after a real execution defect, the workunit should be explicitly reopened/replanned rather than silently repeating multi-gigabyte transfers.

## Download resilience
The workflow uses resumable HTTP transfer (`curl --continue-at -`) because the first full-inventory run observed a transient source disconnect near completion. The current PDOK source supports byte ranges, so a retry should continue from the local partial file rather than restarting at byte zero.

## Admission target
This workunit can be admitted when:
- standard CI is green;
- recursive synthetic tests pass;
- live recursive inventory reaches terminal archive(s) with `depth_limited_zip_member_count == 0`;
- the artifact contains only compact evidence;
- all large temporary ZIP files are removed before upload;
- the actual model-file names/types at the terminal archive level are documented in a canonical checkpoint.

Only then may a separate targeted hydrogeological extraction workunit be designed.
