from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json


QUALIFIED_PARSED_SHA256 = "155db35ac5d7fde4c5ad28e50b7ed3f055b59124e9dcbf4949e110683be3e5c8"

SCREEN_SPECS = {
    "GMW000000004074": {
        "ground_level_m_nap": "7.93",
        "tubes": {
            "tube1": {"screen_top_depth_m_bgl": "2.21", "screen_bottom_depth_m_bgl": "5.21"},
            "tube2": {"screen_top_depth_m_bgl": "11.09", "screen_bottom_depth_m_bgl": "11.59"},
        },
    },
    "GMW000000004104": {
        "ground_level_m_nap": "9.81",
        "tubes": {
            "tube1": {"screen_top_depth_m_bgl": "12.02", "screen_bottom_depth_m_bgl": "14.02"},
            "tube2": {"screen_top_depth_m_bgl": "35.98", "screen_bottom_depth_m_bgl": "37.98"},
        },
    },
}

COLUMN_TO_GMW = {
    "4074_nominal": "GMW000000004074",
    "4074_west_boundary_sensitivity": "GMW000000004074",
    "4104_nominal": "GMW000000004104",
}


def _decimal(value: str, *, context: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal for {context}: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Non-finite decimal for {context}: {value!r}")
    return result


def derive_screen_intervals(specs: dict | None = None) -> dict[str, dict[str, dict]]:
    source = specs or SCREEN_SPECS
    derived: dict[str, dict[str, dict]] = {}
    for gmw, gmw_spec in source.items():
        ground = _decimal(gmw_spec["ground_level_m_nap"], context=f"{gmw}/ground")
        tubes: dict[str, dict] = {}
        for tube, tube_spec in gmw_spec["tubes"].items():
            top_depth = _decimal(tube_spec["screen_top_depth_m_bgl"], context=f"{gmw}/{tube}/top-depth")
            bottom_depth = _decimal(tube_spec["screen_bottom_depth_m_bgl"], context=f"{gmw}/{tube}/bottom-depth")
            if top_depth < 0 or bottom_depth <= top_depth:
                raise ValueError(f"Invalid screen depths for {gmw}/{tube}")
            top_elevation = ground - top_depth
            bottom_elevation = ground - bottom_depth
            tubes[tube] = {
                "ground_level_m_nap": str(ground),
                "screen_top_depth_m_bgl": str(top_depth),
                "screen_bottom_depth_m_bgl": str(bottom_depth),
                "screen_top_m_nap": str(top_elevation),
                "screen_bottom_m_nap": str(bottom_elevation),
                "screen_length_m": str(top_elevation - bottom_elevation),
            }
        derived[gmw] = tubes
    return derived


def _regis_surface_diagnostic(column: dict, bro_ground_m_nap: str) -> dict:
    mv_rows = [row for row in column["layers"] if row["layer"] == "mv"]
    if len(mv_rows) != 1:
        raise ValueError(f"Expected exactly one REGIS mv row, found {len(mv_rows)}")
    token = mv_rows[0].get("top")
    if token is None:
        return {
            "regis_mv_m_nap": None,
            "bro_ground_m_nap": bro_ground_m_nap,
            "regis_minus_bro_ground_m": None,
            "used_for_screen_elevation": False,
        }
    regis_mv = _decimal(token, context="REGIS mv")
    bro_ground = _decimal(bro_ground_m_nap, context="BRO ground")
    return {
        "regis_mv_m_nap": str(regis_mv),
        "bro_ground_m_nap": str(bro_ground),
        "regis_minus_bro_ground_m": str(regis_mv - bro_ground),
        "used_for_screen_elevation": False,
    }


def _screen_overlaps(column: dict, screen: dict) -> dict:
    screen_top = _decimal(screen["screen_top_m_nap"], context="screen top")
    screen_bottom = _decimal(screen["screen_bottom_m_nap"], context="screen bottom")
    screen_length = screen_top - screen_bottom
    if screen_length <= 0:
        raise ValueError("Screen interval must have positive length")

    overlaps: list[dict] = []
    missing_geometry_layers: list[str] = []
    for row in column["layers"]:
        layer = row["layer"]
        if layer == "mv":
            continue
        top_token = row.get("top")
        bottom_token = row.get("bottom")
        if top_token is None or bottom_token is None:
            if top_token is not None or bottom_token is not None:
                missing_geometry_layers.append(layer)
            continue
        layer_top = _decimal(top_token, context=f"{layer}/top")
        layer_bottom = _decimal(bottom_token, context=f"{layer}/bottom")
        if layer_top < layer_bottom:
            raise ValueError(f"Inverted REGIS layer geometry for {layer}: top {layer_top} < bottom {layer_bottom}")
        overlap = min(layer_top, screen_top) - max(layer_bottom, screen_bottom)
        if overlap <= 0:
            continue
        overlaps.append({
            "layer": layer,
            "layer_top_m_nap": str(layer_top),
            "layer_bottom_m_nap": str(layer_bottom),
            "overlap_m": str(overlap),
            "fraction_of_screen": str(overlap / screen_length),
        })

    covered = sum((_decimal(item["overlap_m"], context="overlap") for item in overlaps), Decimal("0"))
    if covered > screen_length:
        raise ValueError(f"Overlapping REGIS geometries double-count screen: covered {covered} > {screen_length}")
    uncovered = screen_length - covered
    return {
        "screen_top_m_nap": str(screen_top),
        "screen_bottom_m_nap": str(screen_bottom),
        "screen_length_m": str(screen_length),
        "overlaps": overlaps,
        "layer_sequence": [item["layer"] for item in overlaps],
        "covered_m": str(covered),
        "uncovered_m": str(uncovered),
        "coverage_complete": uncovered == 0,
        "partial_geometry_layer_count": len(missing_geometry_layers),
        "partial_geometry_layers": missing_geometry_layers,
    }


def qualify_screen_overlap(
    parsed_path: str | Path,
    output_path: str | Path,
    *,
    expected_parsed_sha256: str = QUALIFIED_PARSED_SHA256,
    screen_specs: dict | None = None,
    column_to_gmw: dict[str, str] | None = None,
) -> dict:
    parsed_file = Path(parsed_path)
    payload = parsed_file.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_parsed_sha256:
        raise ValueError(f"Parsed hydro SHA-256 drift: {digest}; expected {expected_parsed_sha256}")
    parsed = json.loads(payload)
    mapping = column_to_gmw or COLUMN_TO_GMW
    if set(parsed["columns"]) != set(mapping):
        raise ValueError(f"Parsed-column membership drift: {sorted(parsed['columns'])} != {sorted(mapping)}")

    screens = derive_screen_intervals(screen_specs)
    results: dict[str, dict] = {}
    for column_id, gmw in mapping.items():
        if gmw not in screens:
            raise ValueError(f"Missing screen specification for {gmw}")
        column = parsed["columns"][column_id]
        bro_ground = next(iter(screens[gmw].values()))["ground_level_m_nap"]
        results[column_id] = {
            "gmw": gmw,
            "x": column["x"],
            "y": column["y"],
            "surface_diagnostic": _regis_surface_diagnostic(column, bro_ground),
            "screens": {tube: _screen_overlaps(column, screen) for tube, screen in screens[gmw].items()},
        }

    comparisons: dict[str, dict] = {}
    nominal = results.get("4074_nominal")
    neighbour = results.get("4074_west_boundary_sensitivity")
    if nominal is not None and neighbour is not None:
        tube_comparisons = {}
        for tube in nominal["screens"]:
            a = nominal["screens"][tube]["layer_sequence"]
            b = neighbour["screens"][tube]["layer_sequence"]
            tube_comparisons[tube] = {
                "nominal_layer_sequence": a,
                "west_neighbour_layer_sequence": b,
                "same_layer_sequence": a == b,
            }
        comparisons["4074_boundary_sensitivity"] = {
            "columns": ["4074_nominal", "4074_west_boundary_sensitivity"],
            "tubes": tube_comparisons,
            "rule": "columns are compared side by side and are never averaged",
        }

    output = {
        "capability": "STAGE_B_REGIS_GEOMETRIC_SCREEN_OVERLAP",
        "dependencies": {
            "parsed_hydro_sha256": digest,
            "parsed_hydro_run": "35133740381",
            "parsed_hydro_artifact_id": "10462726147",
            "ts07_checkpoint": "docs/qualification/TS07_CHECKPOINT.md",
        },
        "screen_intervals": screens,
        "results": results,
        "comparisons": comparisons,
        "guardrails": {
            "geometry_only": True,
            "bro_ground_level_is_screen_elevation_authority": True,
            "regis_mv_used_as_diagnostic_only": True,
            "hydraulic_property_interpretation_performed": False,
            "layer_code_semantics_applied": False,
            "columns_averaged": False,
            "admission_decision_performed": False,
        },
        "qualification_boundary": (
            "Exact vertical screen-to-REGIS interval overlap only. BRO ground level defines screen elevations; REGIS mv is diagnostic only. Layer-code/hydraulic semantics and Stage-B admission remain out of scope."
        ),
    }
    Path(output_path).write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    return output
