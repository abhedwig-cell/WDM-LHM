# Stage-B REGIS II acquisition contract

Status: acquisition probe under qualification.

## Public source

PDOK dataset: BRO REGIS II (HGM)

ATOM entry point:

`https://service.pdok.nl/tno/bro-regis-ii/atom/index.xml`

Official documentation checked 2026-09-16:

- https://www.pdok.nl/introductie/-/article/bro-regis-ii-hgm-
- https://www.pdok.nl/atom-downloadservices/-/article/bro-regis-ii-hgm-
- https://www.bro-productomgeving.nl/bpo/latest/modellen/regis-ii-hydrogeologisch-model-hgm/beschikbare-bro-modellen-regis-ii

The documented current delivery is REGIS II v2.2.3, BRO ID `HGM000000000062`.

## Probe contract

`wdm-lhm-regis-probe`:

1. downloads only ATOM/XML metadata feeds;
2. follows same-host ATOM/XML links to a bounded recursion depth;
3. records archive/download candidates;
4. uses HTTP HEAD where possible to record content length, media type, modification time and ETag;
5. stores SHA-256 hashes of acquired XML bytes;
6. does **not** download the REGIS model archive;
7. makes no hydrogeological interpretation.

## Qualification purpose

The probe must answer before model acquisition is implemented:

- what delivery URLs are currently advertised;
- whether the service can be reached from GitHub Actions;
- how many nested feeds are required;
- what archive(s) are offered;
- approximate archive size and media type;
- whether model acquisition is practical in CI or needs a separate cached/manual acquisition workflow.

## Scientific boundary

REGIS II is regional supporting evidence. PDOK describes the model as a 100 x 100 m hydrogeological model and warns that it is not independently suitable for local street/building-scale interpretation. A successfully extracted REGIS column therefore cannot by itself produce `ADMISSIBLE_FREATIC`.

## Failure policy

- no feed discovered: `BLOCKED_EXTERNAL_SERVICE_OR_CONTRACT`;
- feed discovered but no archive candidate: `BLOCKED_DELIVERY_CONTRACT_UNKNOWN`;
- HEAD unsupported: retain candidate with `head_error`; do not infer zero size;
- multiple candidate archives: retain all; selection requires explicit version/provenance logic;
- missing version identity: do not silently assume the latest documented version.
