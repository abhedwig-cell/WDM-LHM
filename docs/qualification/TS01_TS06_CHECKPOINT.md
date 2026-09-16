# Qualification checkpoint: TS01–TS06

Date: 2026-09-16

## Capability boundary

The current branch contains diagnostic and ingestion capabilities only. It does **not** contain an admitted WDM correction/fusion algorithm and does not claim that statistically post-processed groundwater heads form a new physically consistent LHM/MODFLOW state.

## Synthetic qualification

Local command:

```bash
PYTHONPATH=src pytest -q
```

Current result at bootstrap staging head: **16 passed**.

Covered capabilities include GxG calculation, paired response modelling, observation operators, multiwell batching, regime diagnostics, process-lag diagnostics, real-data admission, and BRO-ingest parsing/contracts.

## Live BRO status

The ChatGPT container used during development could not resolve `api.pdok.nl` because outbound DNS/network access was blocked. This is classified as an execution-environment limitation, not a BRO or algorithm PASS/FAIL.

A GitHub Actions smoke workflow is included to test the same ingest on a GitHub-hosted runner with normal public-network access. The first successful workflow artifact is the required evidence to upgrade TS06 from offline-qualified to live-ingest-qualified.

## Next permitted actions

1. CI must pass on the bootstrap PR.
2. BRO smoke test must either pass or produce a clearly classified external-service/network failure.
3. Merge bootstrap only after the repository is internally coherent.
4. Build a real observation bundle and then pair it with one explicit LHM/MODFLOW run.
5. Run TS05 admission before any real-data diagnostic claim.

## Exclusions

- no national-scale production pipeline;
- no automatic DINO supplementation;
- no WDM fusion/conditioning admission;
- no scenario-transfer claim;
- no physical recalibration claim.
