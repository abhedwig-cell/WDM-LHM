# Stage-B REGIS documentation authority

## Purpose
Extract and inspect exactly one formal documentation file from the already qualified REGIS II v2.2.3 archive chain before assigning semantics to raster filenames or values.

Authority member:
`REGIS II_v02r2s3/Toelichting op de bestanden van REGIS II v2.2.3.pdf`

## Dependency checkpoint
This workunit depends on the admitted recursive inventory in `STAGE_B_REGIS_RECURSIVE_INVENTORY.md` and pins the same archive chain:
- source `brohgm.zip`: size `1,180,207,038` bytes, SHA-256 `1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e`;
- `Model_HGM000000000062.zip`: size `1,179,873,303` bytes, SHA-256 `ad852235b6ae512f8592c7f59126a7d238bb22580c9ce800cd61de1da7919645`;
- `REGIS II_v02r2s3.zip`: size `1,144,397,416` bytes, SHA-256 `c983b244d9fa85478fcb7c3df4900b94e8a0282ac1b238b8081ed0f4bc785ea5`.

The recursive inventory established for the authority PDF:
- declared uncompressed size `900620` bytes;
- CRC32 `0bb0995f`.

Any mismatch fails closed.

## Scientific boundary
This workunit may:
- materialise the two known nested ZIP containers temporarily;
- extract exactly the authority PDF;
- hash, validate, render and read that PDF;
- record formal meanings explicitly stated by the document.

It may not:
- extract or open `.img` rasters;
- read raster values;
- use shapefile/XLSX/XML data as hydrogeological evidence;
- infer local confining conditions for monitoring wells;
- assign `ADMISSIBLE_FREATIC`;
- change Stage-B evidence weights.

## Qualified live execution
Workflow run: `35121003942`

Pre-live qualification:
- ordinary CI: PASS on Python 3.10 and 3.12;
- synthetic nested-ZIP tests: PASS for exact-member extraction and archive-hash drift rejection.

Live result:
- source download: PASS;
- outer archive hash check: PASS;
- model archive hash check: PASS;
- terminal archive hash check: PASS;
- exact authority-member size/CRC checks: PASS;
- extracted non-ZIP members: exactly `1`;
- raster members opened: `0`;
- hydrogeological interpretation performed by extractor: `false`;
- admission decision performed by extractor: `false`;
- large nested archives retained after extraction: `false`.

Extracted authority:
- file: `Toelichting op de bestanden van REGIS II v2.2.3.pdf`;
- size: `900620` bytes;
- CRC32: `0bb0995f`;
- SHA-256: `978adcf645e998a92bd11e33b68e45b6549e8c2b9af91723b5eadf448d31f9b7`;
- document date: `9 January 2025`;
- pages: `4`;
- title/subject: explanation of the files delivered with REGIS II v2.2.3.

Compact workflow artifact:
- artifact ID: `10458561979`;
- artifact ZIP SHA-256: `8c828ba75401cc293497f867bd4a5197e02e8359108192693e7793396783726e`;
- contents: exact authority PDF plus compact provenance/runtime evidence only.

## Admitted file semantics from the package authority
The authority states that the delivery includes raster files for general supporting information and for hydrogeological units. It formally defines the raster suffixes as follows:

| suffix | admitted meaning |
|---|---|
| `-b-c` | elevation of unit base, m relative to NAP |
| `-t-c` | elevation of unit top, m relative to NAP |
| `-d-c` | unit thickness, m |
| `-b-ql` | standard deviation of base elevation, m |
| `-t-ql` | standard deviation of top elevation, m |
| `-d-ql` | standard deviation of thickness, m |
| `-kv-s` | vertical hydraulic conductivity, m/day |
| `-sdv` | standard deviation of vertical hydraulic conductivity, m/day |
| `-c` | resistance, days |
| `-kh-s` | horizontal hydraulic conductivity, m/day |
| `-sdh` | standard deviation of horizontal hydraulic conductivity, m/day |
| `-kd-verz` | transmissivity over the saturated part of the unit, m2/day |

The document also states that:
- the delivery includes a freatic groundwater-level raster expressed in metres relative to NAP;
- that freatic level is used when calculating saturated thickness and therefore transmissivity (`kD`);
- the delivered rasters are ERDAS Imagine files (`.img`, with `.ige` support files possible for large rasters).

These statements admit the file semantics only. They do not by themselves establish the provenance or independence of the freatic surface and do not establish local hydraulic connection at any monitoring well.

## Separate provenance constraint for the freatic surface
A separate TNO REGIS methodology/provenance source documents that, for the REGIS II v2.2 production lineage, the freatic surface was largely derived from Landelijk Hydrologisch Model (LHM) GHG information, with a regional exception for Limburg, and was used to obtain saturated thickness for `kD` calculations.

This provenance is deliberately kept separate from the package-file authority above. Scientific consequence for the WDM/LHM validation workflow:
- `freatisch.img` must **not** receive independent evidential weight when evaluating LHM or declaring a monitoring tube `ADMISSIBLE_FREATIC`;
- using it as independent confirmation would risk recycling LHM-derived information;
- it may still be retained as REGIS internal context/provenance.

For Stage B, the useful independent contribution of REGIS is therefore primarily the regional hydrogeological geometry and hydraulic-layer context: unit top/base/thickness and evidence for poorly permeable or aquifer units around and above a monitoring screen. Direct local and multi-filter observations retain precedence.

## Verdict
**PASS — package-exact REGIS II v2.2.3 documentation authority qualified and raster suffix semantics admitted.**

This verdict admits the meanings above and the authority provenance. It does **not** admit any raster value, hydrogeological interpretation at a monitoring location, or freatic monitoring-well status.

## Next permitted action
Create a separate bounded current-REGIS point-column workunit for the two already qualified Stage-A multi-filter pilot locations:
- `GMW000000004074`, approximately RD `(170300, 440750)`;
- `GMW000000004104`, approximately RD `(169680, 441580)`.

The workunit should acquire only the current REGIS II v2.2.3 hydrogeological column information needed at those locations, preserve the exact requested coordinate and selected grid coordinate/cell, and fail closed on model version, CRS, coordinate ambiguity and missing fields. The first pass should use top/base and hydraulic/confining-layer context; `freatisch.img` is excluded as independent validation evidence.

No `ADMISSIBLE_FREATIC` decision is permitted until that point-column acquisition and interpretation are separately qualified.