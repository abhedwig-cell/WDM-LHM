from pathlib import Path

from wdm_lhm.regis_positive_case_20774 import (
    TARGET_COLUMNS,
    acquire_positive_case_columns,
    build_positive_case_ascii_url,
    build_positive_case_geometry_context,
    parse_positive_case_columns,
)


def _payload(x: str, y: str, *, first_layer: str = "L001") -> bytes:
    layers = ["mv"] + [f"L{i:03d}" for i in range(1, 132)]
    lines = ["Dataset: REGIS.nc"]
    for variable in ("top", "bottom", "kh", "kv", "c"):
        lines.append(f"{variable}.x, {x}")
        for layer in layers:
            if layer == "mv":
                value = "10" if variable == "top" else "-9999"
            elif layer == first_layer:
                values = {"top": "8", "bottom": "6", "kh": "10", "kv": "1", "c": "2"}
                value = values[variable]
            elif layer == "L002":
                values = {"top": "6", "bottom": "4", "kh": "12", "kv": "2", "c": "3"}
                value = values[variable]
            else:
                value = "-9999"
            lines.append(f'{variable}.{variable}[{variable}.layer="{layer}"][{variable}.y={y}], {value}')
    return ("\n".join(lines) + "\n").encode()


def test_target_cells_are_fixed_four_cell_sensitivity_set():
    assert TARGET_COLUMNS == {
        "20774_nominal": {"x_index": 1722, "y_index": 1477, "x": "172200", "y": "447700"},
        "20774_east": {"x_index": 1723, "y_index": 1477, "x": "172300", "y": "447700"},
        "20774_north": {"x_index": 1722, "y_index": 1478, "x": "172200", "y": "447800"},
        "20774_north_east": {"x_index": 1723, "y_index": 1478, "x": "172300", "y": "447800"},
    }


def test_url_requests_only_qualified_context_variables():
    url = build_positive_case_ascii_url("20774_nominal")
    for variable in ("top", "bottom", "kh", "kv", "c"):
        assert f"{variable}[0:1:131]" in url
    for forbidden in ("freatisch", "kD", "hgv", "sdh", "sdv"):
        assert forbidden not in url


def test_acquire_parse_and_geometry_remain_fail_closed(tmp_path: Path):
    by_url = {
        build_positive_case_ascii_url(column_id): _payload(target["x"], target["y"])
        for column_id, target in TARGET_COLUMNS.items()
    }

    def transport(url, headers, timeout_s, max_bytes):
        return by_url[url], {"content-type": "text/plain; charset=UTF-8"}, "https://www.dinodata.nl/opendap/REGIS/REGIS.nc.ascii"

    raw = tmp_path / "raw"
    manifest = acquire_positive_case_columns(raw, get_transport=transport)
    assert len(manifest["responses"]) == 4
    assert manifest["guardrails"]["admission_decision_performed"] is False

    parsed_path = tmp_path / "parsed.json"
    parsed = parse_positive_case_columns(
        raw,
        raw / "regis_positive_20774_manifest.json",
        parsed_path,
    )
    assert set(parsed["columns"]) == set(TARGET_COLUMNS)
    assert parsed["missing_semantics"]["imputation_performed"] is False

    geometry_path = tmp_path / "geometry.json"
    geometry = build_positive_case_geometry_context(parsed_path, geometry_path)
    assert geometry["comparison"]["support_to_screen_geometry_same_sequence_all_columns"] is True
    assert geometry["scientific_boundary"]["regional_context_state"] == "UNKNOWN"
    assert geometry["scientific_boundary"]["hydraulic_continuity_established"] is False
    assert geometry["scientific_boundary"]["admissible_freatic_assigned"] is False


def test_unknown_column_fails_closed():
    try:
        build_positive_case_ascii_url("other")
    except ValueError as exc:
        assert "Unknown positive-case column" in str(exc)
    else:
        raise AssertionError("unknown column should fail")
