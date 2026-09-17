from __future__ import annotations

from bisect import bisect_right
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
import json
import re

from pyproj import CRS


QUALIFIED_COORDINATE_SHA256 = "de1d362c38b6b3e021955580ad024d764e0f9cb5edc637318b450b63c3ce0b1a"
QUALIFIED_DAS_SHA256 = "50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc"
EXPECTED_LENGTHS = {"x": 2646, "y": 2811, "z": 313}
TARGET_RD = {"x": Decimal("172274.997571"), "y": Decimal("447781.978030")}

_STRING_ATTRIBUTE = re.compile(r'^\s*String\s+([A-Za-z_][A-Za-z0-9_]*)\s+"(.*)"\s*;\s*$')


def _parse_decimal(token: str, *, axis: str) -> Decimal:
    try:
        value = Decimal(token.strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid {axis} coordinate token: {token!r}") from exc
    if not value.is_finite():
        raise ValueError(f"non-finite {axis} coordinate: {token!r}")
    return value


def parse_coordinate_ascii(text: str) -> dict[str, tuple[Decimal, ...]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != "Dataset: geotop.nc":
        raise ValueError("unexpected GeoTOP ASCII dataset identity")
    if len(lines) != 4:
        raise ValueError(f"expected dataset identity plus exactly three axis records, got {len(lines)} lines")

    axes: dict[str, tuple[Decimal, ...]] = {}
    for line in lines[1:]:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            raise ValueError(f"malformed GeoTOP axis line: {line[:80]!r}")
        name = parts[0]
        if name not in EXPECTED_LENGTHS:
            raise ValueError(f"unexpected GeoTOP axis record: {name!r}")
        if name in axes:
            raise ValueError(f"duplicate GeoTOP axis record: {name}")
        values = tuple(_parse_decimal(token, axis=name) for token in parts[1:])
        if len(values) != EXPECTED_LENGTHS[name]:
            raise ValueError(
                f"GeoTOP {name} length mismatch: {len(values)} != {EXPECTED_LENGTHS[name]}"
            )
        if any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"GeoTOP {name} axis is not strictly increasing")
        axes[name] = values

    if set(axes) != set(EXPECTED_LENGTHS):
        raise ValueError(f"GeoTOP axis membership mismatch: {sorted(axes)}")
    return axes


def regular_spacing(values: tuple[Decimal, ...], *, axis: str) -> Decimal:
    if len(values) < 2:
        raise ValueError(f"GeoTOP {axis} axis has fewer than two values")
    spacing = values[1] - values[0]
    if spacing <= 0:
        raise ValueError(f"GeoTOP {axis} spacing is not positive")
    for left, right in zip(values[1:], values[2:]):
        if right - left != spacing:
            raise ValueError(f"GeoTOP {axis} axis is not exactly regular")
    return spacing


def _extract_unique_das_section(text: str, name: str) -> str:
    lines = text.splitlines()
    matches: list[str] = []
    for start, line in enumerate(lines):
        if line.strip() != f"{name} {{":
            continue
        depth = 0
        collected: list[str] = []
        for candidate in lines[start:]:
            depth += candidate.count("{")
            depth -= candidate.count("}")
            collected.append(candidate)
            if depth == 0:
                break
        if depth != 0:
            raise ValueError(f"unterminated DAS section for {name}")
        matches.append("\n".join(collected))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one DAS section for {name}, got {len(matches)}")
    return matches[0]


def parse_axis_das_metadata(text: str) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for axis in ("x", "y", "z"):
        section = _extract_unique_das_section(text, axis)
        attrs: dict[str, str] = {}
        for line in section.splitlines()[1:]:
            match = _STRING_ATTRIBUTE.match(line)
            if not match:
                continue
            key, value = match.groups()
            if key in attrs and attrs[key] != value:
                raise ValueError(f"conflicting DAS attribute {axis}.{key}")
            attrs[key] = value
        metadata[axis] = attrs

    for axis in ("x", "y", "z"):
        if metadata[axis].get("epsg") != "7415":
            raise ValueError(f"unexpected GeoTOP {axis} EPSG metadata: {metadata[axis].get('epsg')!r}")
        if metadata[axis].get("units") != "m":
            raise ValueError(f"unexpected GeoTOP {axis} units: {metadata[axis].get('units')!r}")
        if "actual_range" not in metadata[axis]:
            raise ValueError(f"GeoTOP {axis} actual_range missing")
    if metadata["x"].get("standard_name") != "projection_x_coordinate":
        raise ValueError("GeoTOP x standard_name mismatch")
    if metadata["y"].get("standard_name") != "projection_y_coordinate":
        raise ValueError("GeoTOP y standard_name mismatch")
    if metadata["z"].get("reference") != "NAP" or metadata["z"].get("positive") != "up":
        raise ValueError("GeoTOP z vertical-reference metadata mismatch")
    return metadata


def parse_actual_range(raw: str, *, axis: str) -> tuple[Decimal, Decimal]:
    parts = raw.split()
    if len(parts) != 2:
        raise ValueError(f"GeoTOP {axis} actual_range must contain two values")
    lower = _parse_decimal(parts[0], axis=axis)
    upper = _parse_decimal(parts[1], axis=axis)
    if upper <= lower:
        raise ValueError(f"GeoTOP {axis} actual_range is not increasing")
    return lower, upper


def verify_lower_edge_semantics(
    values: tuple[Decimal, ...],
    spacing: Decimal,
    actual_range: tuple[Decimal, Decimal],
    *,
    axis: str,
) -> dict:
    lower, upper = actual_range
    expected_upper = values[-1] + spacing
    if lower != values[0] or upper != expected_upper:
        raise ValueError(
            f"GeoTOP {axis} actual_range is inconsistent with lower-edge sequence: "
            f"range={lower},{upper} values={values[0]},{values[-1]} spacing={spacing}"
        )
    return {
        "semantics": "LOWER_EDGE_SEQUENCE_WITH_EXCLUSIVE_UPPER_RANGE",
        "range_lower": str(lower),
        "range_upper": str(upper),
        "spacing": str(spacing),
    }


def verify_horizontal_crs(epsg: int = 7415) -> dict:
    crs = CRS.from_epsg(epsg)
    if not crs.is_compound:
        raise ValueError(f"GeoTOP EPSG:{epsg} is not a compound CRS in the local PROJ database")
    sub = [(item.to_epsg(), item.name, item.type_name) for item in crs.sub_crs_list]
    horizontal = [item for item in sub if item[0] == 28992]
    if len(horizontal) != 1:
        raise ValueError(f"GeoTOP EPSG:{epsg} does not resolve uniquely to horizontal EPSG:28992: {sub}")
    return {
        "declared_epsg": epsg,
        "compound_crs_name": crs.name,
        "horizontal_epsg": 28992,
        "horizontal_crs_name": horizontal[0][1],
        "sub_crs": [
            {"epsg": code, "name": name, "type": type_name}
            for code, name, type_name in sub
        ],
    }


def map_target_to_lower_edge_axis(
    values: tuple[Decimal, ...],
    actual_range: tuple[Decimal, Decimal],
    target: Decimal,
    *,
    axis: str,
) -> dict:
    lower_range, upper_range = actual_range
    if target < lower_range or target >= upper_range:
        raise ValueError(f"target {axis}={target} lies outside GeoTOP actual_range")
    if target in values[1:]:
        raise ValueError(f"target {axis}={target} lies exactly on an interior GeoTOP cell boundary")

    index = bisect_right(values, target) - 1
    if index < 0 or index >= len(values):
        raise ValueError(f"could not map target {axis}={target} to GeoTOP interval")
    lower = values[index]
    upper = values[index + 1] if index + 1 < len(values) else upper_range
    if not (lower <= target < upper):
        raise ValueError(f"target {axis} mapping invariant failed")
    return {
        "index_zero_based": index,
        "lower_boundary": str(lower),
        "upper_boundary": str(upper),
        "target": str(target),
        "distance_to_lower_boundary": str(target - lower),
        "distance_to_upper_boundary": str(upper - target),
        "exact_boundary_ambiguity": False,
    }


def build_coordinate_mapping(
    coordinate_text: str,
    das_text: str,
) -> dict:
    axes = parse_coordinate_ascii(coordinate_text)
    das = parse_axis_das_metadata(das_text)
    spacing = {name: regular_spacing(values, axis=name) for name, values in axes.items()}
    actual_ranges = {
        name: parse_actual_range(das[name]["actual_range"], axis=name)
        for name in ("x", "y", "z")
    }
    semantics = {
        name: verify_lower_edge_semantics(
            axes[name], spacing[name], actual_ranges[name], axis=name
        )
        for name in ("x", "y", "z")
    }
    crs = verify_horizontal_crs(7415)
    mapping = {
        "x": map_target_to_lower_edge_axis(
            axes["x"], actual_ranges["x"], TARGET_RD["x"], axis="x"
        ),
        "y": map_target_to_lower_edge_axis(
            axes["y"], actual_ranges["y"], TARGET_RD["y"], axis="y"
        ),
    }
    minimum_distance = min(
        Decimal(mapping["x"]["distance_to_lower_boundary"]),
        Decimal(mapping["x"]["distance_to_upper_boundary"]),
        Decimal(mapping["y"]["distance_to_lower_boundary"]),
        Decimal(mapping["y"]["distance_to_upper_boundary"]),
    )
    return {
        "axis_lengths": {name: len(values) for name, values in axes.items()},
        "axis_spacing_m": {name: str(value) for name, value in spacing.items()},
        "axis_semantics": semantics,
        "crs": crs,
        "target_rd": {name: str(value) for name, value in TARGET_RD.items()},
        "horizontal_mapping": mapping,
        "boundary_sensitivity": {
            "minimum_horizontal_boundary_distance_m": str(minimum_distance),
            "exact_boundary_ambiguity": False,
            "generic_near_boundary_threshold_used": False,
            "neighbour_sensitivity_required_by_exact_boundary_rule": False,
            "note": "Exact distances are retained; no arbitrary near-boundary threshold is introduced.",
        },
        "z_summary_only": {
            "lower": str(actual_ranges["z"][0]),
            "upper_exclusive": str(actual_ranges["z"][1]),
            "spacing_m": str(spacing["z"]),
            "screen_or_q95_correlation_performed": False,
        },
    }


def qualify_coordinate_mapping(
    coordinate_file: str | Path,
    das_file: str | Path,
    output_file: str | Path,
) -> dict:
    coordinate_path = Path(coordinate_file)
    das_path = Path(das_file)
    coordinate_bytes = coordinate_path.read_bytes()
    das_bytes = das_path.read_bytes()
    coordinate_digest = sha256(coordinate_bytes).hexdigest()
    das_digest = sha256(das_bytes).hexdigest()
    if coordinate_digest != QUALIFIED_COORDINATE_SHA256:
        raise ValueError(
            f"GeoTOP coordinate raw SHA drift: {coordinate_digest} != {QUALIFIED_COORDINATE_SHA256}"
        )
    if das_digest != QUALIFIED_DAS_SHA256:
        raise ValueError(f"GeoTOP DAS SHA drift: {das_digest} != {QUALIFIED_DAS_SHA256}")

    result = build_coordinate_mapping(
        coordinate_bytes.decode("utf-8", errors="strict"),
        das_bytes.decode("utf-8", errors="strict"),
    )
    manifest = {
        "capability": "STAGE_B_GEOTOP_20774_COORDINATE_MAPPING",
        "state": "COORDINATE_MAPPING_QUALIFIED_NO_GEOLOGICAL_INTERPRETATION",
        "dependencies": {
            "coordinate_sha256": coordinate_digest,
            "das_sha256": das_digest,
        },
        "mapping": result,
        "guardrails": {
            "categorical_voxel_values_requested": False,
            "strat_requested": False,
            "lithok_requested": False,
            "screen_correlation_performed": False,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
