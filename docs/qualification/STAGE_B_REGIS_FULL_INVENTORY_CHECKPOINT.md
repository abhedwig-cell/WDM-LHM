# Stage-B REGIS full-inventory checkpoint

## Capability
One-time inventory of the first nested REGIS model archive without persisting national model data.

## Canonical source state
- base: `main` at `6f2ea38e5e1d09a0f99f313493a0c233b81d11e3`
- work branch: `work/regis-full-inventory`
- qualified code head before this checkpoint: `e15456eae6792dc216b4c1cda61ecdda68a48f87`
- source delivery: `https://service.pdok.nl/tno/bro-regis-ii/atom/downloads/brohgm.zip`
- source ETag: `0x8DE8992A0B37BF8`
- source size: `1,180,207,038` bytes

## Qualification
- GitHub Actions run: `35114169497`
- full-inventory job: `104855211686`
- result: PASS
- compact evidence artifact: `10455643914`
- CI: PASS on Python 3.10 and 3.12
- test suite: 31/31 PASS

## Immutable source/evidence hashes
Outer `brohgm.zip`:
- SHA-256: `1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e`

First nested model archive `Model_HGM000000000062.zip`:
- outer-member compressed size: `1,180,168,461` bytes
- uncompressed size: `1,179,873,303` bytes
- CRC32: `5512a75a`
- SHA-256 after bounded temporary extraction: `ad852235b6ae512f8592c7f59126a7d238bb22580c9ce800cd61de1da7919645`

## Observed archive structure
`Model_HGM000000000062.zip` contains 9 root files:
- 8 documentation/report PDFs;
- 1 further nested model archive: `REGIS II_v02r2s3.zip`.

For `REGIS II_v02r2s3.zip`:
- compressed size inside `Model_HGM000000000062.zip`: `1,087,591,073` bytes;
- uncompressed size: `1,144,397,416` bytes;
- CRC32: `5d3997b3`.

The actual model grids/files are therefore still one archive level deeper than this workunit inventoried.

## Guardrails actually satisfied
- no non-ZIP model member was extracted;
- no hydrogeological value was interpreted;
- no freatic admission decision was made;
- the outer and temporarily materialised nested large ZIPs were removed on the ephemeral runner before artifact upload;
- only compact CSV/JSON/provenance evidence was persisted;
- uploaded evidence artifact was only a few kilobytes, not model data.

## Runtime observation
The public source download was the dominant cost. The initial transfer failed near completion and the retry restarted from byte zero because the workflow did not yet use resumable `curl -C -`. A subsequent recursive-inventory workunit should use resumable download semantics to avoid repeating transferred bytes after a transient source disconnect.

## Verdict
**PASS for first-level full inventory only.**

This checkpoint does not qualify REGIS hydrogeological interpretation and does not admit any monitoring tube as `ADMISSIBLE_FREATIC`.

## Next permitted action
Create a separate recursive-inventory workunit that, in one ephemeral runner execution:
1. downloads the current outer delivery once using resumable transfer;
2. recursively materialises ZIP containers only;
3. inventories every archive level until the first non-ZIP model files are visible;
4. extracts no non-ZIP model member;
5. deletes all large temporary ZIPs;
6. persists only compact recursive inventory/provenance evidence.

Only after that recursive inventory may a targeted hydrogeological extraction workunit be designed.
