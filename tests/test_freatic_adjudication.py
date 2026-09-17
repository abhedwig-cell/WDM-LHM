from wdm_lhm.freatic_adjudication import (
    AdjudicationVerdict,
    EvidenceAvailability,
    RegionalContextState,
    ScreenRelation,
    StageBFreaticEvidence,
    ValidationLineageState,
    ValidationUseState,
    VerticalHydraulicInterpretation,
    adjudicate_stage_b,
    assess_validation_use,
)


def _evidence(station_id: str, **overrides) -> StageBFreaticEvidence:
    values = dict(
        station_id=station_id,
        direct_observations=EvidenceAvailability.AVAILABLE,
        screen_relation=ScreenRelation.SUPPORTS_FREE_SURFACE,
        time_series_usable=True,
        construction_metadata=EvidenceAvailability.AVAILABLE,
        multi_filter_evidence=EvidenceAvailability.AVAILABLE,
        vertical_interpretation=VerticalHydraulicInterpretation.NO_DISTINCT_REGIME_EVIDENCE,
        regional_context=RegionalContextState.NOT_USED,
    )
    values.update(overrides)
    return StageBFreaticEvidence(**values)


def test_q1_4104_tube1_is_not_admissible():
    # Qualified case: screen 12.02-14.02 m-mv versus q95 3.620 m-mv;
    # Tube1-Tube2 median head difference +0.12 m, sign fraction 0.937.
    evidence = _evidence(
        "GMW000000004104:1",
        screen_relation=ScreenRelation.CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT,
        vertical_interpretation=VerticalHydraulicInterpretation.CANDIDATE_DISTINCT_DEEPER_REGIME,
        regional_context=RegionalContextState.SUPPORTING_STABLE,
    )
    result = adjudicate_stage_b(evidence)
    assert result.verdict == AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC


def test_q2_4104_tube2_is_not_admissible():
    # Qualified case: screen 35.98-37.98 m-mv; full REGIS overlap in
    # NUPZ-WAz1 is supporting context and cannot create local admission.
    evidence = _evidence(
        "GMW000000004104:2",
        screen_relation=ScreenRelation.CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT,
        vertical_interpretation=VerticalHydraulicInterpretation.CANDIDATE_DISTINCT_DEEPER_REGIME,
        regional_context=RegionalContextState.SUPPORTING_STABLE,
    )
    result = adjudicate_stage_b(evidence)
    assert result.verdict == AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC


def test_q3_4074_tube1_preserves_ambiguity():
    # Qualified case: screen 2.21-5.21 m-mv versus q95 2.794 m-mv;
    # Tube1-Tube2 median difference +0.27 m, sign fraction 0.981; REGIS
    # assignment differs materially across a cell boundary about 5.6 mm away.
    evidence = _evidence(
        "GMW000000004074:1",
        screen_relation=ScreenRelation.LONG_SCREEN_AMBIGUOUS,
        vertical_interpretation=VerticalHydraulicInterpretation.VERTICAL_STRUCTURE_PRESENT,
        regional_context=RegionalContextState.SPATIALLY_UNSTABLE,
    )
    result = adjudicate_stage_b(evidence)
    assert result.verdict == AdjudicationVerdict.REVIEW_REQUIRED
    assert "REGIONAL_CONTEXT_SPATIALLY_UNSTABLE" in result.reason_codes


def test_q4_4074_tube2_is_not_admissible_despite_regis_cell_agreement():
    # Qualified case: deep 11.09-11.59 m-mv screen and persistent separation
    # from Tube 1. Both REGIS columns place it in NUgsc, but regional agreement
    # is not positive proof of local freatic representativeness.
    evidence = _evidence(
        "GMW000000004074:2",
        screen_relation=ScreenRelation.CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT,
        vertical_interpretation=VerticalHydraulicInterpretation.CANDIDATE_DISTINCT_DEEPER_REGIME,
        regional_context=RegionalContextState.SUPPORTING_STABLE,
    )
    result = adjudicate_stage_b(evidence)
    assert result.verdict == AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC


def test_missing_required_evidence_stays_insufficient_not_negative():
    evidence = _evidence(
        "UNKNOWN",
        direct_observations=EvidenceAvailability.UNKNOWN,
        screen_relation=ScreenRelation.UNKNOWN,
    )
    result = adjudicate_stage_b(evidence)
    assert result.verdict == AdjudicationVerdict.INSUFFICIENT_EVIDENCE
    assert "DIRECT_OBSERVATION_EVIDENCE_NOT_AVAILABLE" in result.reason_codes


def test_legacy_heuristic_does_not_control_adjudication():
    base = _evidence(
        "LEGACY",
        screen_relation=ScreenRelation.LONG_SCREEN_AMBIGUOUS,
        vertical_interpretation=VerticalHydraulicInterpretation.VERTICAL_STRUCTURE_PRESENT,
        legacy_heuristic_flag=False,
    )
    flagged = StageBFreaticEvidence(**{**base.__dict__, "legacy_heuristic_flag": True})
    assert adjudicate_stage_b(base).verdict == AdjudicationVerdict.REVIEW_REQUIRED
    assert adjudicate_stage_b(flagged).verdict == AdjudicationVerdict.REVIEW_REQUIRED


def test_local_non_freatic_evidence_has_precedence_over_regional_instability():
    evidence = _evidence(
        "PRECEDENCE",
        screen_relation=ScreenRelation.CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT,
        vertical_interpretation=VerticalHydraulicInterpretation.CANDIDATE_DISTINCT_DEEPER_REGIME,
        regional_context=RegionalContextState.SPATIALLY_UNSTABLE,
    )
    assert adjudicate_stage_b(evidence).verdict == AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC


def test_positive_path_is_gated_until_separately_qualified():
    evidence = _evidence("POSITIVE")
    assert adjudicate_stage_b(evidence).verdict == AdjudicationVerdict.REVIEW_REQUIRED
    assert adjudicate_stage_b(evidence, allow_admissible=True).verdict == AdjudicationVerdict.ADMISSIBLE_FREATIC


def test_validation_lineage_is_separate_from_hydraulic_adjudication():
    evidence = _evidence("POSITIVE")
    admitted = adjudicate_stage_b(evidence, allow_admissible=True)
    assert assess_validation_use(admitted, ValidationLineageState.VALIDATION_INDEPENDENCE_SUPPORTED) == ValidationUseState.ELIGIBLE
    assert assess_validation_use(admitted, ValidationLineageState.VALIDATION_INDEPENDENCE_UNKNOWN) == ValidationUseState.REVIEW_LINEAGE
    assert assess_validation_use(admitted, ValidationLineageState.VALIDATION_DEPENDENCE_PRESENT) == ValidationUseState.NOT_ELIGIBLE_LINEAGE

    review = adjudicate_stage_b(_evidence("REVIEW", screen_relation=ScreenRelation.LONG_SCREEN_AMBIGUOUS))
    assert assess_validation_use(review, ValidationLineageState.VALIDATION_INDEPENDENCE_SUPPORTED) == ValidationUseState.NOT_ELIGIBLE_HYDRAULIC
