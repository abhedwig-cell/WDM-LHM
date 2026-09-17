from decimal import Decimal
from pathlib import Path
import hashlib

import pytest

from wdm_lhm.regis_hydro_parse import (
    MISSING_SENTINEL,
    VARIABLES,
    parse_regis_hydro_ascii,
    parsed_column_to_dict,
    qualify_hydro_columns,
)


def _payload(*, x: str = "170300", y: str = "440700") -> bytes:
    layers = ("A", "B", "C")
    values = {
        "top": ("8.15", "5.03", MISSING_SENTINEL),
        "bottom": ("7.67", "3.96", MISSING_SENTINEL),
        "kh": ("7.89", MISSING_SENTINEL, "-9999.0"),
        "kv": (MISSING_SENTINEL, "0.01", MISSING_SENTINEL),
        "c": (MISSING_SENTINEL, "100", MISSING_SENTINEL),
    }
    lines = ["Dataset: REGIS.nc"]
    # Deliberately different from request/canonical variable order.
    for variable in ("c", "top", "kv", "bottom", "kh"):
        lines.append(f"{variable}.x, {x}")
        for layer, token in zip(layers, values[variable], strict=True):
            lines.append(
                f'{variable}.{variable}[{variable}.layer="{layer}"][{variable}.y={y}], {token}'
            )
    return ("\n".join(lines) + "\n").encode()


def test_parser_is_name_based_and_maps_only_exact_missing_sentinel():
    parsed = parse_regis_hydro_ascii(_payload(), expected_layer_count=3)
    assert parsed.x == Decimal("170300")
    assert parsed.y == Decimal("440700")
    assert parsed.layers == ("A", "B", "C")
    assert parsed.values["top"]["C"] is None
    # Exact-token policy: -9999.0 is a finite observed numeric token, not silently reclassified.
    assert parsed.values["kh"]["C"] == Decimal("-9999.0")
    rendered = parsed_column_to_dict(parsed)
    assert rendered["present_counts"] == {"top": 2, "bottom": 2, "kh": 2, "kv": 1, "c": 1}


def test_parser_fails_closed_on_unknown_or_duplicate_records():
    with pytest.raises(ValueError, match="Unexpected DAP2 ASCII record"):
        parse_regis_hydro_ascii(_payload() + b"mystery, 1\n", expected_layer_count=3)

    duplicate = _payload() + b'top.top[top.layer="A"][top.y=440700], 1\n'
    with pytest.raises(ValueError, match="Duplicate top/A"):
        parse_regis_hydro_ascii(duplicate, expected_layer_count=3)


def test_parser_fails_closed_on_layer_order_or_coordinate_drift():
    payload = _payload().decode()
    # Reverse two layer rows inside the kh block only.
    a = 'kh.kh[kh.layer="A"][kh.y=440700], 7.89\nkh.kh[kh.layer="B"][kh.y=440700], -9999'
    b = 'kh.kh[kh.layer="B"][kh.y=440700], -9999\nkh.kh[kh.layer="A"][kh.y=440700], 7.89'
    with pytest.raises(ValueError, match="Layer-order drift"):
        parse_regis_hydro_ascii(payload.replace(a, b), expected_layer_count=3)

    y_drift = payload.replace(
        'top.top[top.layer="B"][top.y=440700], 5.03',
        'top.top[top.layer="B"][top.y=440701], 5.03',
    )
    with pytest.raises(ValueError, match="Y-coordinate drift"):
        parse_regis_hydro_ascii(y_drift, expected_layer_count=3)


def test_bundle_qualification_pins_raw_hash_coordinates_and_provenance(tmp_path: Path):
    raw = _payload()
    filename = "column.ascii.txt"
    (tmp_path / filename).write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    expected = {
        "test": {
            "filename": filename,
            "sha256": digest,
            "x": "170300",
            "y": "440700",
        }
    }
    output = tmp_path / "parsed.json"
    result = qualify_hydro_columns(
        tmp_path,
        output,
        qualified_columns=expected,
        expected_layer_count=3,
    )
    assert result["columns"]["test"]["source"]["sha256"] == digest
    assert result["missing_semantics"]["raw_missing_token"] == "-9999"
    assert result["guardrails"]["screen_to_unit_mapping_performed"] is False
    assert output.is_file()

    bad = {"test": {**expected["test"], "sha256": "0" * 64}}
    with pytest.raises(ValueError, match="Raw SHA-256 drift"):
        qualify_hydro_columns(
            tmp_path,
            tmp_path / "bad.json",
            qualified_columns=bad,
            expected_layer_count=3,
        )


def test_bundle_qualification_requires_same_layer_labels_between_columns(tmp_path: Path):
    first = _payload(x="170300")
    second = _payload(x="170200").replace(b'layer="C"', b'layer="D"')
    (tmp_path / "a.txt").write_bytes(first)
    (tmp_path / "b.txt").write_bytes(second)
    expected = {
        "a": {
            "filename": "a.txt",
            "sha256": hashlib.sha256(first).hexdigest(),
            "x": "170300",
            "y": "440700",
        },
        "b": {
            "filename": "b.txt",
            "sha256": hashlib.sha256(second).hexdigest(),
            "x": "170200",
            "y": "440700",
        },
    }
    with pytest.raises(ValueError, match="Layer-label drift between qualified columns"):
        qualify_hydro_columns(
            tmp_path,
            tmp_path / "out.json",
            qualified_columns=expected,
            expected_layer_count=3,
        )
