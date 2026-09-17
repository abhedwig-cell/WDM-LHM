from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from wdm_lhm.geotop_column_parse import (
    EXPECTED_LENGTH,
    EXPECTED_RECORDS,
    LITHOK_MISSING,
    STRAT_MISSING,
    parse_geotop_single_column,
)


def _fixture_bytes(*, strat=None, lithok=None, z_override=None, record_override=None) -> bytes:
    z = z_override or [str(-50 + 0.5 * i).rstrip('0').rstrip('.') if '.' in str(-50 + 0.5 * i) else str(-50 + 0.5 * i) for i in range(EXPECTED_LENGTH)]
    # Preserve integer-looking decimals without trailing .0.
    z = [str(int(float(v))) if float(v).is_integer() else str(v) for v in z]
    strat_values = strat or [STRAT_MISSING] * EXPECTED_LENGTH
    lithok_values = lithok or [LITHOK_MISSING] * EXPECTED_LENGTH
    names = list(EXPECTED_RECORDS)
    if record_override is not None:
        names[record_override[0]] = record_override[1]
    lines = [
        'Dataset: geotop.nc',
        names[0] + ', ' + ', '.join(z),
        names[1] + ', ' + ', '.join(str(v) for v in strat_values),
        names[2] + ', ' + ', '.join(z),
        names[3] + ', ' + ', '.join(str(v) for v in lithok_values),
    ]
    return ('\n'.join(lines) + '\n').encode('utf-8')


def _parse_fixture(tmp_path: Path, payload: bytes):
    raw = tmp_path / 'raw.txt'
    out = tmp_path / 'parsed.json'
    raw.write_bytes(payload)
    return parse_geotop_single_column(raw, out, expected_sha256=sha256(payload).hexdigest())


def test_valid_structure_and_missing_normalization(tmp_path: Path):
    strat = [STRAT_MISSING] * EXPECTED_LENGTH
    lithok = [LITHOK_MISSING] * EXPECTED_LENGTH
    strat[0] = 5120
    strat[1] = -127
    lithok[0] = 5
    lithok[1] = 0
    result = _parse_fixture(tmp_path, _fixture_bytes(strat=strat, lithok=lithok))
    assert result['state'] == 'SINGLE_COLUMN_PARSED_CODES_UNINTERPRETED'
    assert result['column']['strat_code'][0] == 5120
    assert result['column']['strat_code'][1] == -127
    assert result['column']['strat_code'][2] is None
    assert result['column']['lithok_code'][0] == 5
    assert result['column']['lithok_code'][1] == 0
    assert result['column']['lithok_code'][2] is None
    assert result['guardrails']['class_codes_interpreted'] is False
    assert result['guardrails']['hydraulic_interpretation_performed'] is False
    assert result['guardrails']['allow_admissible_enabled'] is False


def test_default_production_sha_is_pinned(tmp_path: Path):
    payload = _fixture_bytes()
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='SHA mismatch'):
        parse_geotop_single_column(raw, tmp_path / 'out.json')


def test_extra_record_fails_closed(tmp_path: Path):
    payload = _fixture_bytes() + b'extra, 1\n'
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='exactly 5 logical lines'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())


def test_record_name_or_xy_label_drift_fails_closed(tmp_path: Path):
    payload = _fixture_bytes(record_override=(1, 'strat.strat[strat.x=172300][strat.y=447700]'))
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='record-name/order drift'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())


def test_z_axis_mismatch_fails_closed(tmp_path: Path):
    z = [str(-50 + 0.5 * i) for i in range(EXPECTED_LENGTH)]
    z[10] = '-44.75'
    payload = _fixture_bytes(z_override=z)
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='qualified Gate-2 z axis'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())


def test_class_length_mismatch_fails_closed(tmp_path: Path):
    strat = [STRAT_MISSING] * (EXPECTED_LENGTH - 1)
    payload = _fixture_bytes(strat=strat)
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='length mismatch'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())


def test_non_integer_class_token_fails_closed(tmp_path: Path):
    payload = _fixture_bytes().replace(b', 0, 0, 0,', b', 0, 1.5, 0,', 1)
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='non-integer token'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())


def test_dataset_line_drift_fails_closed(tmp_path: Path):
    payload = _fixture_bytes().replace(b'Dataset: geotop.nc', b'Dataset: other.nc', 1)
    raw = tmp_path / 'raw.txt'
    raw.write_bytes(payload)
    with pytest.raises(ValueError, match='dataset line'):
        parse_geotop_single_column(raw, tmp_path / 'out.json', expected_sha256=sha256(payload).hexdigest())
