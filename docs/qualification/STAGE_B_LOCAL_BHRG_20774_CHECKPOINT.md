# Stage-B local BHR-G evidence checkpoint

Status: **QUALIFIED_LOCAL_BHRG_ACQUISITION_NO_LOCAL_OBJECTS**

Date: 2026-09-17

## Capability

`STAGE_B_LOCAL_BHRG_20774_ACQUISITION`

This checkpoint qualifies bounded local BRO BHR-G discovery and raw-object acquisition for `GMW000000020774` only. It does not interpret lithology, infer hydraulic continuity, or assign `ADMISSIBLE_FREATIC`.

## Canonical source

- repository: `abhedwig-cell/WDM-LHM`
- canonical main at workunit start: `9d67355056cf0f6cfe927e55767b34ff8bdbad7e`
- branch: `work/stage-b-local-bhrg-20774`
- qualified implementation head: `f6bbfa4872f7f806956684d63c62e82b00a93ad2`
- parent capability: `STAGE_B_POSITIVE_ADMISSION_CASE_20774`
- parent verdict: `QUALIFIED_REGIS_CONTEXT_POSITIVE_ADMISSION_NOT_ESTABLISHED`
- parent tracking surface: issue #4

## Reused immutable target evidence

The target remains fixed to the admitted PR #11 evidence:

- GMW: `GMW000000020774`
- station: `GMW000000020774_T1`
- RD coordinate: `x=172274.997571 m`, `y=447781.978030 m`
- deterministic WGS84 transform: `lon=5.638863172`, `lat=52.018122914`
- BRO ground level: `9.85 m NAP`
- empirical q95 groundwater depth: `2.054 m-mv`
- screen: `3.330–4.330 m-mv`

No broad GMW/BRO rediscovery was performed.

## Acquisition authority and bounded geometry

The public BRO BHR-G REST service is pinned to:

- base service: `https://publiek.broservices.nl/sr/bhrg/v3`
- local discovery operation: `POST /characteristics/searches?requestReference=...`
- object retrieval operation: `GET /objects/{BRO-ID}`

The live search used one fixed enclosing circle of `0.5 km` around the qualified target coordinate, with a hard result guardrail of `25` objects.

The `0.5 km` radius is an acquisition window only. It is not a geological correlation distance, hydraulic threshold or admission criterion.

## Implementation qualification

Ordinary CI run `35186288533`: **PASS** on the implementation head.

- Python 3.10.21: **83 passed** in 9.07 s;
- Python 3.12.14: **83 passed** in 10.35 s.

The added tests qualify:

- deterministic RD-to-WGS84 transformation;
- exact fixed characteristics URL and request geometry;
- namespace-independent BRO-ID extraction;
- valid zero-result handling;
- duplicate-ID and over-limit rejection;
- pinned object URL construction;
- raw request/response/object hash persistence;
- object BRO-ID mismatch rejection;
- redirect drift rejection;
- absence of lithological, hydraulic and admission interpretation in the capability output.

## Live qualification

Live workflow run `35186288607`: **PASS**.

Artifact:

- ID: `10482651227`;
- name: `stage-b-local-bhrg-20774-35186288607`;
- ZIP size: `1700` bytes;
- artifact digest SHA-256: `5fb4f90925d1a3c62aa6a40f350cd3e3b210c7ee0cda15d934fa7f78ac161212`.

Persisted members:

- `bhrg_characteristics_request.json`;
- `bhrg_characteristics_response.xml`;
- `bhrg_local_manifest.json`.

Immutable live hashes:

- request SHA-256: `caac101944244e535f83dab07d2436242aeaba1733ad7f5b925dd8630c316c64`;
- characteristics response SHA-256: `c3acf6ceebd499f8f046b36130836bed0865be9fe5ac44af1ac26e6693d7ecd4`;
- characteristics response bytes: `613`;
- content type: `application/xml`.

## Live scientific evidence state

The bounded live search returned:

- state: `NO_LOCAL_BHRG_FOUND`;
- result count: `0`;
- BRO BHR-G identifiers: none;
- raw BHR-G object XML files: none;
- total object bytes: `0`.

This is a qualified statement about the specific BHR-G query only. It is **not** evidence that no local geological layer exists and it is **not** evidence for absence of a confining interval.

In particular, this result must not be converted into favourable Stage-B evidence for `GMW000000020774_T1`.

## Guardrails retained

The live manifest confirms:

- source: `BRO_BHR_G_PUBLIC_REST`;
- raw-only acquisition: `true`;
- lithology interpretation performed: `false`;
- hydraulic interpretation performed: `false`;
- screen correlation performed: `false`;
- interpolation performed: `false`;
- GeoTOP used: `false`;
- admission decision performed: `false`;
- `allow_admissible` enabled: `false`.

No search-radius expansion was performed after the zero-result response.

## Verdict

**PASS — LOCAL BHR-G ACQUISITION QUALIFIED; NO LOCAL BHR-G OBJECTS FOUND IN THE FIXED 0.5 KM ACQUISITION WINDOW.**

The capability and its negative evidence boundary are qualified. The monitoring tube is not admitted as freatic.

`GMW000000020774_T1` therefore remains **not positively admitted** under Stage B because the required affirmative local hydraulic-continuity evidence is still absent.

## Mutations admitted by this checkpoint

- `src/wdm_lhm/bhrg_local_acquisition.py`;
- `src/wdm_lhm/bhrg_local_acquisition_cli.py`;
- `tests/test_bhrg_local_acquisition.py`;
- `.github/workflows/bhrg-local-20774.yml`;
- this qualification checkpoint.

These mutations add evidence acquisition only. They do not alter the Stage-B adjudication operator.

## Next permitted action

After this checkpoint is admitted to `main`, start a **separate GeoTOP/local high-resolution geological acquisition workunit** for `GMW000000020774`.

That workunit must:

1. use a formally identified current public GeoTOP authority/service;
2. acquire only the smallest reproducible point/column evidence needed around the fixed target;
3. persist raw source identity, request geometry, version/provenance and immutable hashes before interpretation;
4. keep acquisition and lithological/hydraulic interpretation separate;
5. leave `ADMISSIBLE_FREATIC` and `allow_admissible=True` unchanged.

Do not broaden the BHR-G radius merely to obtain a positive result, and do not mix GeoTOP acquisition into this branch.

## Exclusions

This checkpoint does not:

- interpret absence of BHR-G records scientifically;
- classify sediment, lithology or stratigraphy;
- infer permeability from material names;
- correlate a geological interval to the monitoring screen;
- interpolate between geological observations;
- use or interpret GeoTOP;
- change Stage-B evidence precedence;
- assign `ADMISSIBLE_FREATIC`;
- enable automatic positive admission.