# WDM-LHM

Research software for diagnosing and, only where justified, combining information from the BRO Model Grondwaterspiegeldiepte (WDM), transient LHM/MODFLOW simulations and groundwater monitoring time series.

## Status

**Status A-light bootstrap / diagnostic research software.** The repository currently implements TS01–TS06: paired time-series diagnostics, multiwell observation operators, regime and process diagnostics, real-data admission, and BRO/PDOK ingestion. It does **not** yet contain an admitted WDM fusion or correction model.

TS06 has been technically qualified against the live public BRO/PDOK services through GitHub Actions. This qualifies data ingestion, not the hydrological suitability or independence of automatically selected monitoring tubes. See [`docs/qualification/LIVE_BRO_QUALIFICATION.md`](docs/qualification/LIVE_BRO_QUALIFICATION.md).

The scientific documentation is deliberately separated into:

- [`docs/THEORY.md`](docs/THEORY.md)
- [`docs/CONCEPTUAL_MODEL.md`](docs/CONCEPTUAL_MODEL.md)
- [`docs/FORMAL_MODEL.md`](docs/FORMAL_MODEL.md)
- [`docs/DATA_LINEAGE.md`](docs/DATA_LINEAGE.md)
- [`docs/STATUS_A_LIGHT.md`](docs/STATUS_A_LIGHT.md)
- [`docs/architecture/TRACEABILITY.md`](docs/architecture/TRACEABILITY.md)
- [`docs/qualification/TS01_TS06_CHECKPOINT.md`](docs/qualification/TS01_TS06_CHECKPOINT.md)

## Install and test

```bash
python -m pip install -e . pytest
pytest -q
```

The current bootstrap baseline is 17 tests.

## Main commands

Single-station synthetic demo:

```bash
wdm-lhm demo output/demo
```

Multiwell synthetic demo:

```bash
wdm-lhm demo-multi output/demo_multi
```

Real-data admission:

```bash
wdm-lhm admit observations.csv model_timeseries.csv stations.csv cells.csv forcing.csv output/admission \
  --flux-metadata flux_metadata.csv \
  --run-metadata run_metadata.csv
```

BRO/PDOK ingest:

```bash
wdm-lhm bro-ingest output/bro_pilot \
  --bbox 5.60,51.94,5.75,52.02 \
  --min-observations 100 \
  --min-span-days 730 \
  --max-series 25
```

A GitHub Actions workflow provides live BRO execution so results do not depend on the network restrictions of a chat/container environment.

## Scientific guardrail

A statistically improved groundwater series is not automatically a physically consistent MODFLOW/LHM state. Direct observations, WDM predictions and model-cell states have different support and may share source information. Those dependencies are treated as part of the method, not as optional metadata.
