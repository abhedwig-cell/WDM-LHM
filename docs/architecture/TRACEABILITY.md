# Scientific traceability matrix

| Capability | Theory / conceptual basis | Formal construct | Implementation | Qualification |
| --- | --- | --- | --- | --- |
| Coordinate/sign normalization | `THEORY.md` §2 | `FORMAL_MODEL.md` §1 | `conventions.py`, `io.py` | `test_pipeline.py`, `test_gxg.py` |
| GxG diagnostics | `THEORY.md` §3 | `FORMAL_MODEL.md` §3 | `gxg.py` | `test_gxg.py` |
| Paired response identification | `THEORY.md` §4 | `FORMAL_MODEL.md` §4 | `response_model.py`, `pipeline.py` | `test_response.py`, `test_pipeline.py` |
| Observation operator | `CONCEPTUAL_MODEL.md` | `FORMAL_MODEL.md` §2 | `observation_operator.py` | `test_observation_operator.py`, `test_operator_fluxes.py` |
| Multiwell batch | `CONCEPTUAL_MODEL.md` | station-wise application | `batch.py` | `test_batch.py` |
| Regime analysis | `THEORY.md` §5 | `FORMAL_MODEL.md` §6 | `regime_analysis.py`, `regimes.py` | `test_regime_analysis.py` |
| Process diagnosis | `THEORY.md` §5 | `FORMAL_MODEL.md` §7 | `process_diagnosis.py` | `test_process_diagnosis.py` |
| Admission gate | `DATA_LINEAGE.md` | `FORMAL_MODEL.md` §8 | `admission.py` | `test_admission.py` |
| BRO/PDOK ingest | `DATA_LINEAGE.md` | source contract | `bro_ingest.py` | `test_bro_ingest.py`; live Actions smoke pending |
| WDM conditioning | not yet admitted | not canonical | none | blocked pending real-data evidence |
