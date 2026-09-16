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
| BRO/PDOK ingest | `DATA_LINEAGE.md` | source contract | `bro_ingest.py` | `test_bro_ingest.py`, `test_bro_catalog_semantics.py`; live Actions smoke PASS |
| TS07 Stage-A freatic candidate screening | `qualification/FREATIC_SCREENING_THEORY.md`, `qualification/FREATIC_SCREENING_CONCEPTUAL_MODEL.md` | `qualification/FREATIC_SCREENING_FORMAL_MODEL.md` | `freatic_screening.py`, CLI `freatic-prescreen` | `test_freatic_screening.py`, `test_bro_catalog_semantics.py`; `qualification/TS07_CHECKPOINT.md`; live TS07 smoke PASS |
| Stage-B hydrogeological evidence model | `qualification/STAGE_B_FREATIC_THEORY.md`, `qualification/STAGE_B_FREATIC_CONCEPTUAL_MODEL.md` | `qualification/STAGE_B_FREATIC_FORMAL_MODEL.md` | evidence contracts only | design basis; automatic final admission remains **not admitted** |
| Stage-B REGIS acquisition metadata | Stage-B evidence hierarchy and REGIS regional-support boundary | `qualification/STAGE_B_FREATIC_FORMAL_MODEL.md` §4, §7, §8; `qualification/STAGE_B_REGIS_ACQUISITION.md` | `regis_probe.py`, `remote_zip.py`, `remote_zip_extract.py` and separate CLIs | `test_regis_probe.py`, `test_remote_zip.py`, `test_remote_zip_extract.py`; `qualification/STAGE_B_REGIS_ACQUISITION_CHECKPOINT.md`; live REGIS probe/range/extract PASS |
| TS07 Stage-B final freatic admission | same Stage-B theory/conceptual basis | fail-closed admission outputs in `qualification/STAGE_B_FREATIC_FORMAL_MODEL.md` | no automatic admission rule | **not yet admitted**; requires selective hydrogeological evidence extraction and known-case qualification |
| WDM conditioning | not yet admitted | not canonical | none | blocked pending real-data evidence |
