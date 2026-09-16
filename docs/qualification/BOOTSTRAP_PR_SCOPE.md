# Bootstrap PR scope

This PR establishes the first canonical WDM-LHM repository baseline.

## In scope

- TS01–TS06 diagnostic and ingest code;
- 16 synthetic/unit qualification tests;
- Status A-light theory, conceptual model, formal model, data lineage and traceability documentation;
- BRO/PDOK service contract;
- real-pilot input contracts/templates;
- CI on Python 3.10 and 3.12;
- live BRO/PDOK smoke test using a small Wageningen-area bbox.

## Out of scope

- WDM-conditioned transient correction;
- physical recalibration of LHM/MODFLOW;
- scenario-transfer claims;
- national operational deployment;
- automatic interpretation of BRO/DINO lineage as independent evidence.

## Admission condition

Merge only after ordinary CI passes and the BRO smoke test is either successful or has a clearly attributable external-service/network failure that does not invalidate repository code.
