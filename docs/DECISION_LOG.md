# Decision log

## D-001 — Repository as canonical project surface

**Decision:** GitHub becomes the canonical location for code, scientific documentation, tests, qualification evidence and future workunits.

**Reason:** execution and scientific decisions must be reviewable and reproducible rather than distributed across chat-generated archives.

## D-002 — Status A-light structure

**Decision:** maintain separate theory, conceptual-model, formal-model and implementation layers.

**Reason:** prevents software behaviour from becoming an undocumented scientific assumption.

## D-003 — Diagnosis before fusion

**Decision:** TS01–TS06 stop before WDM-conditioned transient correction.

**Reason:** dependency, support and process-error structure must first be demonstrated on real data.

## D-004 — Explicit observation operator

**Decision:** station/model comparison always passes through an explicit operator with spatial QC.

**Reason:** point and model-cell support are not equivalent.

## D-005 — GitHub Actions for live BRO execution

**Decision:** use GitHub-hosted Actions for reproducible BRO/PDOK smoke and later pilot ingestion.

**Reason:** development container has outbound network restrictions; repository execution should not depend on that environment.
