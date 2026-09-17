from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json


QUALIFIED_RAW_COLUMN_SHA256 = "ad7acee0b57acd428f6df3d7dd6104d94c267a7ddc11b65798446db7dfebb0a8"
EXPECTED_DATASET_LINE = "Dataset: geotop.nc"
EXPECTED_LENGTH = 313
EXPECTED_X_LOWER_BOUND = 172200
EXPECTED_Y_LOWER_BOUND = 447700
STRAT_MISSING = 0
LITHOK_MISSING = -127

EXPECTED_RECORDS = (
    "strat.z",
    f"strat.strat[strat.x={EXPECTED_X_LOWER_BOUND}][strat.y={EXPECTED_Y_LOWER_BOUND}]",
    "lithok.z",
    f"lithok.lithok[lithok.x={EXPECTED_X_LOWER_BOUND}][lithok.y={EXPECTED_Y_LOWER_BOUND}]",
)


def _expected_z_axis() -> list[Decimal]:
    start = Decimal("-50")
    step = Decimal("0.5")
    return [start + step * i for i in range(EXPECTED_LENGTH)]


def _split_record(line: str) -> tuple[str, list[str]]:
    if "," not in line:
        raise ValueError(f"GeoTOP column record has no comma separator: {line!r}")
    name, values = line.split(",", 1)
    tokens = [token.strip() for token in values.split(",")]
    if not name or not tokens or any(token == "" for token in tokens):
        raise ValueError(f"Malformed GeoTOP column record: {name!r}")
    return name.strip(), tokens


def _parse_z(tokens: list[str], record_name: str) -> list[Decimal]:
    if len(tokens) != EXPECTED_LENGTH:
        raise ValueError(f"{record_name} length mismatch: {len(tokens)} != {EXPECTED_LENGTH}")
    values: list[Decimal] = []
    for token in tokens:
        try:
            value = Decimal(token)
        except InvalidOperation as exc:
            raise ValueError(f"{record_name} contains invalid decimal token {token!r}") from exc
        if not value.is_finite():
            raise ValueError(f"{record_name} contains non-finite z value")
        values.append(value)
    expected = _expected_z_axis()
    if values != expected:
        raise ValueError(f"{record_name} does not equal qualified Gate-2 z axis")
    return values


def _parse_int_vector(tokens: list[str], record_name: str) -> list[int]:
    if len(tokens) != EXPECTED_LENGTH:
        raise ValueError(f"{record_name} length mismatch: {len(tokens)} != {EXPECTED_LENGTH}")
    values: list[int] = []
    for token in tokens:
        if token.startswith("+"):
            body = token[1:]
        elif token.startswith("-"):
            body = token[1:]
        else:
            body = token
        if not body.isdigit():
            raise ValueError(f"{record_name} contains non-integer token {token!r}")
        values.append(int(token))
    return values


def parse_geotop_single_column(
    raw_file: str | Path,
    output_file: str | Path,
    *,
    expected_sha256: str = QUALIFIED_RAW_COLUMN_SHA256,
) -> dict:
    """Parse the immutable Gate-3A GeoTOP column without geological interpretation.

    Production callers use the pinned SHA. The optional expected SHA exists only
    to permit deterministic synthetic unit fixtures; the production CLI does not
    expose it.
    """
    raw_path = Path(raw_file)
    payload = raw_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"GeoTOP raw column SHA mismatch: {digest} != {expected_sha256}")

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("GeoTOP raw column is not valid UTF-8") from exc

    lines = text.splitlines()
    if len(lines) != 5:
        raise ValueError(f"GeoTOP raw column must contain exactly 5 logical lines, found {len(lines)}")
    if lines[0] != EXPECTED_DATASET_LINE:
        raise ValueError(f"Unexpected GeoTOP dataset line: {lines[0]!r}")

    parsed_records = [_split_record(line) for line in lines[1:]]
    record_names = tuple(name for name, _ in parsed_records)
    if record_names != EXPECTED_RECORDS:
        raise ValueError(f"GeoTOP column record-name/order drift: {record_names!r}")

    record_map = {name: tokens for name, tokens in parsed_records}
    strat_z = _parse_z(record_map[EXPECTED_RECORDS[0]], EXPECTED_RECORDS[0])
    strat_raw = _parse_int_vector(record_map[EXPECTED_RECORDS[1]], EXPECTED_RECORDS[1])
    lithok_z = _parse_z(record_map[EXPECTED_RECORDS[2]], EXPECTED_RECORDS[2])
    lithok_raw = _parse_int_vector(record_map[EXPECTED_RECORDS[3]], EXPECTED_RECORDS[3])
    if strat_z != lithok_z:
        raise ValueError("strat.z and lithok.z differ")

    strat = [None if value == STRAT_MISSING else value for value in strat_raw]
    lithok = [None if value == LITHOK_MISSING else value for value in lithok_raw]

    result = {
        "capability": "STAGE_B_GEOTOP_20774_SINGLE_COLUMN_PARSE",
        "state": "SINGLE_COLUMN_PARSED_CODES_UNINTERPRETED",
        "raw_dependency": {
            "sha256": digest,
            "bytes": len(payload),
            "source_file": raw_path.name,
            "gate_3a_head": "384175e92a026e6511bb7faba26687ab44b3f9aa",
        },
        "mapping_dependency": {
            "gate_2b_head": "e22babf0dfea9dead8301c50a6bd439400663826",
            "x_index_zero_based": 1586,
            "y_index_zero_based": 1092,
            "x_lower_bound_m": EXPECTED_X_LOWER_BOUND,
            "y_lower_bound_m": EXPECTED_Y_LOWER_BOUND,
            "z_count": EXPECTED_LENGTH,
        },
        "missing_semantics": {
            "strat_raw_missing_token": STRAT_MISSING,
            "lithok_raw_missing_token": LITHOK_MISSING,
            "normalized_representation": None,
            "authority": "qualified Gate-1 DAS metadata",
        },
        "column": {
            "z_m_nap": [str(value) for value in strat_z],
            "strat_code": strat,
            "lithok_code": lithok,
        },
        "structural_summary": {
            "count": EXPECTED_LENGTH,
            "strat_missing_count": sum(value is None for value in strat),
            "lithok_missing_count": sum(value is None for value in lithok),
            "strat_distinct_non_missing_codes": sorted({value for value in strat if value is not None}),
            "lithok_distinct_non_missing_codes": sorted({value for value in lithok if value is not None}),
        },
        "guardrails": {
            "raw_sha_verified": True,
            "record_structure_verified": True,
            "qualified_z_axis_verified": True,
            "x_y_labels_verified": True,
            "missing_tokens_normalized_only": True,
            "class_codes_interpreted": False,
            "geological_names_assigned": False,
            "probability_or_uncertainty_used": False,
            "screen_correlation_performed": False,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }

    out = Path(output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
