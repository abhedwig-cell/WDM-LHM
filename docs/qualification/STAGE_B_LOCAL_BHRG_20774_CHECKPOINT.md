# Stage-B local BHR-G evidence checkpoint

Status: **DESIGN_LOCAL_BHRG_ACQUISITION_PENDING_LIVE**

Date: 2026-09-17

## Capability

`STAGE_B_LOCAL_BHRG_20774_ACQUISITION`

This is the next bounded decision surface after PR #11. It acquires local geological borehole evidence for `GMW000000020774` only. It does not interpret lithology, infer hydraulic continuity, or assign `ADMISSIBLE_FREATIC`.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start: `9d67355056cf0f6cfe927e55767b34ff8bdbad7e`
- branch: `work/stage-b-local-bhrg-20774`
- parent capability: `STAGE_B_POSITIVE_ADMISSION_CASE_20774`
- parent verdict: `QUALIFIED_REGIS_CONTEXT_POSITIVE_ADMISSION_NOT_ESTABLISHED`
- parent tracking surface: issue #4

## Reused immutable target evidence

The target remains fixed to the admitted PR #11 evidence:

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m` (rounded from qualified TS07 evidence)
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW/BRO rediscovery is permitted in this workunit.

## Acquisition authority

The public BRO BHR-G REST service is the bounded acquisition channel:

- base service: `https://publiek.broservices.nl/sr/bhrg/v3`
- local discovery operation: `POST /characteristics/searches?requestReference=...`
- object retrieval operation: `GET /objects/{BRO-ID}`

The service is intended for incidental public retrieval, not bulk tiling. This workunit therefore uses one fixed local search around the target and hard maximum-result guardrails.

## Bounded search geometry

The target RD coordinate is deterministically transformed from `EPSG:28992` to `EPSG:4326` for the REST `enclosingCircle` request.

Acquisition radius: **0.5 km**.

This radius is an acquisition window only. It is not a geological correlation distance, not a hydraulic threshold, and not an admission criterion.

If the result count exceeds the fixed guardrail, the acquisition fails closed rather than truncating or choosing nearest records heuristically.

## Acquisition contract

The first live workunit may only:

1. submit one BHR-G characteristics request for the fixed target circle;
2. retain the raw characteristics XML and SHA-256;
3. parse only BRO identifiers needed for deterministic follow-up retrieval;
4. retrieve the complete public BHR-G object XML for every returned BRO-ID when the count remains within the fixed guardrail;
5. retain each raw object and SHA-256;
6. emit a compact manifest with request geometry, object membership, raw hashes, byte counts and endpoint provenance.

The implementation must not:

- classify sediment, lithology or stratigraphy;
- infer permeability from material names;
- correlate a borehole layer to the monitoring screen;
- interpolate between boreholes;
- treat absence of a nearby BHR-G record as evidence of absence of a confining layer;
- use GeoTOP in the same acquisition phase;
- change Stage-B evidence precedence;
- assign `ADMISSIBLE_FREATIC` or enable `allow_admissible=True`.

## Fail-closed conditions

Acquisition must fail closed on:

- endpoint drift away from the fixed public BHR-G service;
- malformed or unexpected XML;
- duplicate BRO identifiers;
- result count above the fixed maximum;
- object-response BRO-ID mismatch;
- empty/malformed object payloads;
- transport errors or HTTP redirects outside the fixed host/path family.

A valid zero-result response is retained as `NO_LOCAL_BHRG_FOUND`; it is not interpreted scientifically.

## Qualification plan

Synthetic qualification must cover:

- exact characteristics URL and JSON request geometry;
- deterministic RD -> WGS84 transformation;
- namespace-independent BRO-ID extraction;
- zero-result handling;
- duplicate and over-limit rejection;
- fixed object URL construction;
- per-object hash/provenance persistence;
- proof that the capability emits no lithological/hydraulic interpretation field.

Live qualification must run on the same PR head as ordinary CI.

## Verdict

**DESIGN_LOCAL_BHRG_ACQUISITION_PENDING_LIVE**

## Next permitted action

Implement and qualify the bounded BHR-G acquisition capability exactly as above. Only after raw local objects are qualified may a separate interpretation workunit inspect whether those objects contain usable local material intervals spanning the q95-to-screen interval.

If no usable BHR-G objects are available locally, stop this branch at that evidence boundary and open a separate GeoTOP acquisition workunit instead of mixing sources.