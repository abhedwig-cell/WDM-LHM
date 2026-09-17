from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CONTRADICTORY = "CONTRADICTORY"


class ScreenRelation(str, Enum):
    """Qualified relation of screen support to the local fluctuation zone.

    These are interpretive evidence states, not numeric depth thresholds.
    """

    SUPPORTS_FREE_SURFACE = "SUPPORTS_FREE_SURFACE"
    LONG_SCREEN_AMBIGUOUS = "LONG_SCREEN_AMBIGUOUS"
    CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT = "CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT"
    UNKNOWN = "UNKNOWN"


class VerticalHydraulicInterpretation(str, Enum):
    NO_DISTINCT_REGIME_EVIDENCE = "NO_DISTINCT_REGIME_EVIDENCE"
    VERTICAL_STRUCTURE_PRESENT = "VERTICAL_STRUCTURE_PRESENT"
    CANDIDATE_DISTINCT_DEEPER_REGIME = "CANDIDATE_DISTINCT_DEEPER_REGIME"
    UNKNOWN = "UNKNOWN"


class RegionalContextState(str, Enum):
    NOT_USED = "NOT_USED"
    SUPPORTING_STABLE = "SUPPORTING_STABLE"
    SPATIALLY_UNSTABLE = "SPATIALLY_UNSTABLE"
    CONTRADICTORY = "CONTRADICTORY"
    UNKNOWN = "UNKNOWN"


class AdjudicationVerdict(str, Enum):
    ADMISSIBLE_FREATIC = "ADMISSIBLE_FREATIC"
    NOT_ADMISSIBLE_FREATIC = "NOT_ADMISSIBLE_FREATIC"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ValidationLineageState(str, Enum):
    VALIDATION_INDEPENDENCE_SUPPORTED = "VALIDATION_INDEPENDENCE_SUPPORTED"
    VALIDATION_INDEPENDENCE_UNKNOWN = "VALIDATION_INDEPENDENCE_UNKNOWN"
    VALIDATION_DEPENDENCE_PRESENT = "VALIDATION_DEPENDENCE_PRESENT"


class ValidationUseState(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE_HYDRAULIC = "NOT_ELIGIBLE_HYDRAULIC"
    NOT_ELIGIBLE_LINEAGE = "NOT_ELIGIBLE_LINEAGE"
    REVIEW_LINEAGE = "REVIEW_LINEAGE"


@dataclass(frozen=True)
class StageBFreaticEvidence:
    """Typed, already-qualified evidence presented to Stage-B adjudication.

    The dataclass deliberately does not derive hydraulic meaning from REGIS
    layer codes, numerical head differences, or legacy depth thresholds. Those
    transformations belong to separately qualified evidence-producing steps.
    """

    station_id: str
    direct_observations: EvidenceAvailability
    screen_relation: ScreenRelation
    time_series_usable: bool | None
    construction_metadata: EvidenceAvailability
    multi_filter_evidence: EvidenceAvailability = EvidenceAvailability.NOT_APPLICABLE
    vertical_interpretation: VerticalHydraulicInterpretation = VerticalHydraulicInterpretation.UNKNOWN
    regional_context: RegionalContextState = RegionalContextState.NOT_USED
    legacy_heuristic_flag: bool | None = None
    validation_lineage: ValidationLineageState = ValidationLineageState.VALIDATION_INDEPENDENCE_UNKNOWN


@dataclass(frozen=True)
class StageBAdjudicationResult:
    station_id: str
    verdict: AdjudicationVerdict
    reason_codes: tuple[str, ...]


def _insufficient_required_evidence(evidence: StageBFreaticEvidence) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence.direct_observations != EvidenceAvailability.AVAILABLE:
        reasons.append("DIRECT_OBSERVATION_EVIDENCE_NOT_AVAILABLE")
    if evidence.construction_metadata != EvidenceAvailability.AVAILABLE:
        reasons.append("CONSTRUCTION_METADATA_NOT_AVAILABLE")
    if evidence.time_series_usable is None:
        reasons.append("TIME_SERIES_USABILITY_UNKNOWN")
    elif not evidence.time_series_usable:
        reasons.append("TIME_SERIES_NOT_USABLE")
    if evidence.screen_relation == ScreenRelation.UNKNOWN:
        reasons.append("SCREEN_RELATION_UNKNOWN")
    return tuple(reasons)


def adjudicate_stage_b(
    evidence: StageBFreaticEvidence,
    *,
    allow_admissible: bool = False,
) -> StageBAdjudicationResult:
    """Apply the qualitative Stage-B evidence contract.

    `allow_admissible` defaults to False because the current real-data
    qualification set contains adversarial review/non-admission cases but no
    separately qualified positive automatic-admission case. The gate prevents
    production promotion of absence-of-contradiction into positive admission.
    """

    insufficient = _insufficient_required_evidence(evidence)
    if insufficient:
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.INSUFFICIENT_EVIDENCE,
            reason_codes=insufficient,
        )

    # Higher-priority direct + same-location evidence can establish a robust
    # non-freatic/deeper interpretation. Regional context cannot override it.
    if evidence.vertical_interpretation == VerticalHydraulicInterpretation.CANDIDATE_DISTINCT_DEEPER_REGIME:
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC,
            reason_codes=("POSITIVE_DISTINCT_DEEPER_REGIME_EVIDENCE",),
        )

    if (
        evidence.screen_relation == ScreenRelation.CLEARLY_BELOW_LOCAL_FLUCTUATION_SUPPORT
        and evidence.multi_filter_evidence == EvidenceAvailability.AVAILABLE
        and evidence.vertical_interpretation == VerticalHydraulicInterpretation.VERTICAL_STRUCTURE_PRESENT
    ):
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.NOT_ADMISSIBLE_FREATIC,
            reason_codes=("SCREEN_BELOW_LOCAL_FLUCTUATION_SUPPORT", "VERTICAL_STRUCTURE_PRESENT"),
        )

    # Known ambiguity remains explicit. A coarse regional model may expose or
    # reinforce uncertainty but cannot resolve it by averaging or override.
    review_reasons: list[str] = []
    if evidence.screen_relation == ScreenRelation.LONG_SCREEN_AMBIGUOUS:
        review_reasons.append("LONG_SCREEN_SPANS_DEEPER_INTERVAL")
    if evidence.vertical_interpretation == VerticalHydraulicInterpretation.VERTICAL_STRUCTURE_PRESENT:
        review_reasons.append("VERTICAL_STRUCTURE_PRESENT")
    if evidence.regional_context == RegionalContextState.SPATIALLY_UNSTABLE:
        review_reasons.append("REGIONAL_CONTEXT_SPATIALLY_UNSTABLE")
    elif evidence.regional_context == RegionalContextState.CONTRADICTORY:
        review_reasons.append("REGIONAL_CONTEXT_CONTRADICTORY")

    if review_reasons:
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.REVIEW_REQUIRED,
            reason_codes=tuple(dict.fromkeys(review_reasons)),
        )

    positive_path = (
        evidence.direct_observations == EvidenceAvailability.AVAILABLE
        and evidence.screen_relation == ScreenRelation.SUPPORTS_FREE_SURFACE
        and evidence.time_series_usable is True
        and evidence.construction_metadata == EvidenceAvailability.AVAILABLE
        and evidence.vertical_interpretation == VerticalHydraulicInterpretation.NO_DISTINCT_REGIME_EVIDENCE
        and evidence.regional_context not in {RegionalContextState.SPATIALLY_UNSTABLE, RegionalContextState.CONTRADICTORY}
    )

    if positive_path and allow_admissible:
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.ADMISSIBLE_FREATIC,
            reason_codes=("POSITIVE_LOCAL_FREATIC_SUPPORT",),
        )

    if positive_path:
        return StageBAdjudicationResult(
            station_id=evidence.station_id,
            verdict=AdjudicationVerdict.REVIEW_REQUIRED,
            reason_codes=("POSITIVE_PATH_NOT_YET_ADMITTED",),
        )

    return StageBAdjudicationResult(
        station_id=evidence.station_id,
        verdict=AdjudicationVerdict.REVIEW_REQUIRED,
        reason_codes=("FREATIC_REPRESENTATIVENESS_NOT_PROVEN",),
    )


def assess_validation_use(
    adjudication: StageBAdjudicationResult,
    lineage: ValidationLineageState,
) -> ValidationUseState:
    """Keep hydraulic representativeness separate from validation lineage."""

    if adjudication.verdict != AdjudicationVerdict.ADMISSIBLE_FREATIC:
        return ValidationUseState.NOT_ELIGIBLE_HYDRAULIC
    if lineage == ValidationLineageState.VALIDATION_DEPENDENCE_PRESENT:
        return ValidationUseState.NOT_ELIGIBLE_LINEAGE
    if lineage == ValidationLineageState.VALIDATION_INDEPENDENCE_SUPPORTED:
        return ValidationUseState.ELIGIBLE
    return ValidationUseState.REVIEW_LINEAGE
