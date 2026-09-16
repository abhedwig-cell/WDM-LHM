from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import hashlib
import json
import re


QUALIFIED_COORDINATE_SHA256 = "fa39271a98fefa2091483b7247d53e3744e1e26e478969310ce6f3560725c7f3"
EXPECTED_X = 2800
EXPECTED_Y = 3250
EXPECTED_LAYERS = 132

TS07_TARGETS = {
    "GMW000000004074": {
        "x": "170300.00558661332",
        "y": "440749.9888647009",
        "ground_level_m_nap": "7.93",
    },
    "GMW000000004104": {
        "x": "169680.00087220868",
        "y": "441579.98838886514",
        "ground_level_m_nap": "9.81",
    },
}


@dataclass(frozen=True)
class RegisGrid:
    dataset: str
    x: tuple[Decimal, ...]
    y: tuple[Decimal, ...]
    layers: tuple[str, ...]
    x_bounds: tuple[tuple[Decimal, Decimal], ...]
    y_bounds: tuple[tuple[Decimal, Decimal], ...]


@dataclass(frozen=True)
class AxisLocation:
    value: str
    status: str
    index: int | None
    candidate_indices: tuple[int, ...]
    lower: str | None
    upper: str | None
    distance_to_lower_m: str | None
    distance_to_upper_m: str | None
    nearest_boundary: str | None
    nearest_boundary_distance_m: str | None
    adjacent_index_across_nearest_boundary: int | None

    def as_dict(self) -> dict:
        return asdict(self)


def _decimal(text: str) -> Decimal:
    try:
        return Decimal(text.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal value: {text!r}") from exc


def _csv_row(line: str) -> list[str]:
    return next(csv.reader([line], skipinitialspace=True))


def parse_regis_coordinate_ascii(
    payload: bytes | str,
    *,
    expected_x: int = EXPECTED_X,
    expected_y: int = EXPECTED_Y,
    expected_layers: int = EXPECTED_LAYERS,
) -> RegisGrid:
    """Parse the exact DAP2 ASCII structure emitted by the qualified REGIS dataset."""
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    dataset: str | None = None
    x: tuple[Decimal, ...] | None = None
    y: tuple[Decimal, ...] | None = None
    layers: tuple[str, ...] | None = None
    x_bounds_by_index: dict[int, tuple[Decimal, Decimal]] = {}
    y_bounds_by_index: dict[int, tuple[Decimal, Decimal]] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Dataset:"):
            dataset = line.split(":", 1)[1].strip()
            continue
        if line.startswith("x,"):
            x = tuple(_decimal(v) for v in _csv_row(line)[1:])
            continue
        if line.startswith("y,"):
            y = tuple(_decimal(v) for v in _csv_row(line)[1:])
            continue
        if line.startswith("layer,"):
            layers = tuple(v.strip() for v in _csv_row(line)[1:])
            continue

        match = re.fullmatch(
            r"(x_bounds|y_bounds)\[(\d+)\],\s*([^,]+),\s*([^,]+)",
            line,
        )
        if match:
            name, index_text, lower_text, upper_text = match.groups()
            target = x_bounds_by_index if name == "x_bounds" else y_bounds_by_index
            index = int(index_text)
            if index in target:
                raise ValueError(f"Duplicate {name}[{index}]")
            target[index] = (_decimal(lower_text), _decimal(upper_text))

    if dataset is None or x is None or y is None or layers is None:
        raise ValueError("Coordinate response is missing dataset/x/y/layer")
    if len(x) != expected_x or len(y) != expected_y or len(layers) != expected_layers:
        raise ValueError(
            f"Dimension mismatch: x={len(x)}, y={len(y)}, layer={len(layers)}; "
            f"expected {expected_x}/{expected_y}/{expected_layers}"
        )
    if set(x_bounds_by_index) != set(range(expected_x)):
        raise ValueError("x bounds are incomplete or non-contiguous in index space")
    if set(y_bounds_by_index) != set(range(expected_y)):
        raise ValueError("y bounds are incomplete or non-contiguous in index space")

    x_bounds = tuple(x_bounds_by_index[i] for i in range(expected_x))
    y_bounds = tuple(y_bounds_by_index[i] for i in range(expected_y))
    _validate_axis("x", x, x_bounds)
    _validate_axis("y", y, y_bounds)

    return RegisGrid(
        dataset=dataset,
        x=x,
        y=y,
        layers=layers,
        x_bounds=x_bounds,
        y_bounds=y_bounds,
    )


def _validate_axis(
    name: str,
    coordinates: tuple[Decimal, ...],
    bounds: tuple[tuple[Decimal, Decimal], ...],
) -> None:
    previous_upper: Decimal | None = None
    for index, (coordinate, (lower, upper)) in enumerate(zip(coordinates, bounds, strict=True)):
        if not lower < upper:
            raise ValueError(f"{name}_bounds[{index}] is not increasing: {lower}, {upper}")
        if not lower <= coordinate <= upper:
            raise ValueError(
                f"{name}[{index}]={coordinate} falls outside its bounds [{lower}, {upper}]"
            )
        if previous_upper is not None and lower != previous_upper:
            raise ValueError(
                f"{name} bounds are not exactly contiguous between indices {index - 1} and {index}: "
                f"{previous_upper} != {lower}"
            )
        previous_upper = upper


def locate_axis(
    value: str | Decimal,
    bounds: tuple[tuple[Decimal, Decimal], ...],
) -> AxisLocation:
    """Locate a coordinate from explicit bounds without imposing a near-boundary tolerance."""
    coordinate = value if isinstance(value, Decimal) else _decimal(str(value))
    if coordinate < bounds[0][0] or coordinate > bounds[-1][1]:
        raise ValueError(
            f"Coordinate {coordinate} falls outside grid bounds [{bounds[0][0]}, {bounds[-1][1]}]"
        )

    for index, (lower, upper) in enumerate(bounds):
        if lower < coordinate < upper:
            distance_lower = coordinate - lower
            distance_upper = upper - coordinate
            if distance_lower <= distance_upper:
                nearest_boundary = lower
                nearest_distance = distance_lower
                adjacent_index = index - 1 if index > 0 else None
            else:
                nearest_boundary = upper
                nearest_distance = distance_upper
                adjacent_index = index + 1 if index + 1 < len(bounds) else None
            return AxisLocation(
                value=str(coordinate),
                status="INSIDE_CELL",
                index=index,
                candidate_indices=(index,),
                lower=str(lower),
                upper=str(upper),
                distance_to_lower_m=str(distance_lower),
                distance_to_upper_m=str(distance_upper),
                nearest_boundary=str(nearest_boundary),
                nearest_boundary_distance_m=str(nearest_distance),
                adjacent_index_across_nearest_boundary=adjacent_index,
            )

        if coordinate == lower:
            if index == 0:
                return AxisLocation(
                    value=str(coordinate),
                    status="ON_OUTER_BOUNDARY",
                    index=0,
                    candidate_indices=(0,),
                    lower=str(lower),
                    upper=str(upper),
                    distance_to_lower_m="0",
                    distance_to_upper_m=str(upper - coordinate),
                    nearest_boundary=str(lower),
                    nearest_boundary_distance_m="0",
                    adjacent_index_across_nearest_boundary=None,
                )
            return AxisLocation(
                value=str(coordinate),
                status="ON_INTERNAL_BOUNDARY",
                index=None,
                candidate_indices=(index - 1, index),
                lower=None,
                upper=None,
                distance_to_lower_m=None,
                distance_to_upper_m=None,
                nearest_boundary=str(coordinate),
                nearest_boundary_distance_m="0",
                adjacent_index_across_nearest_boundary=None,
            )

        if index == len(bounds) - 1 and coordinate == upper:
            return AxisLocation(
                value=str(coordinate),
                status="ON_OUTER_BOUNDARY",
                index=index,
                candidate_indices=(index,),
                lower=str(lower),
                upper=str(upper),
                distance_to_lower_m=str(coordinate - lower),
                distance_to_upper_m="0",
                nearest_boundary=str(upper),
                nearest_boundary_distance_m="0",
                adjacent_index_across_nearest_boundary=None,
            )

    raise ValueError(f"Coordinate {coordinate} could not be located within the qualified bounds")


def build_target_mapping(grid: RegisGrid) -> dict[str, dict]:
    targets: dict[str, dict] = {}
    for gmwid, metadata in TS07_TARGETS.items():
        x_location = locate_axis(metadata["x"], grid.x_bounds)
        y_location = locate_axis(metadata["y"], grid.y_bounds)
        nominal_cell = None
        if x_location.index is not None and y_location.index is not None:
            nominal_cell = {"x_index": x_location.index, "y_index": y_location.index}
        targets[gmwid] = {
            "rd_x_m": metadata["x"],
            "rd_y_m": metadata["y"],
            "ground_level_m_nap": metadata["ground_level_m_nap"],
            "x": x_location.as_dict(),
            "y": y_location.as_dict(),
            "nominal_cell": nominal_cell,
        }
    return targets


def qualify_coordinate_mapping(
    raw_path: str | Path,
    output_path: str | Path,
    *,
    expected_sha256: str = QUALIFIED_COORDINATE_SHA256,
) -> dict:
    raw = Path(raw_path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError(
            f"Coordinate evidence SHA-256 drift: {digest}; expected {expected_sha256}"
        )

    grid = parse_regis_coordinate_ascii(raw)
    if grid.dataset != "REGIS.nc":
        raise ValueError(f"Unexpected dataset label: {grid.dataset!r}")

    mapping = {
        "capability": "STAGE_B_REGIS_COORDINATE_MAPPING",
        "coordinate_evidence_sha256": digest,
        "dataset": grid.dataset,
        "dimensions": {"x": len(grid.x), "y": len(grid.y), "layer": len(grid.layers)},
        "grid_extent_from_bounds": {
            "x_min": str(grid.x_bounds[0][0]),
            "x_max": str(grid.x_bounds[-1][1]),
            "y_min": str(grid.y_bounds[0][0]),
            "y_max": str(grid.y_bounds[-1][1]),
        },
        "layers": list(grid.layers),
        "targets": build_target_mapping(grid),
        "decision_semantics": {
            "point_to_cell_basis": "explicit x_bounds/y_bounds from qualified REGIS coordinate response",
            "exact_internal_boundary": "ambiguous; return both candidate cells and no nominal index",
            "near_boundary": (
                "report exact distance and adjacent cell only; no universal sensitivity threshold is introduced"
            ),
        },
        "guardrails": {
            "hydrogeological_model_values_requested": False,
            "freatic_surface_requested": False,
            "hydrogeological_interpretation_performed": False,
            "admission_decision_performed": False,
        },
    }
    Path(output_path).write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
    return mapping
