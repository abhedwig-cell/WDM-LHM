from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json
import re


VARIABLES = ("top", "bottom", "kh", "kv", "c")
MISSING_SENTINEL = "-9999"
EXPECTED_LAYER_COUNT = 132

QUALIFIED_RAW_COLUMNS = {
    "4074_nominal": {
        "filename": "regis_hydro_4074_nominal.ascii.txt",
        "sha256": "fbb7cf9bf77abbb268fb9cf38f709ee400923693f165e5d292f656f0e5bfc2aa",
        "x": "170300",
        "y": "440700",
    },
    "4074_west_boundary_sensitivity": {
        "filename": "regis_hydro_4074_west_boundary_sensitivity.ascii.txt",
        "sha256": "79a6c28d741bd5993a56475b117e95c69903ac1e4d506e504b394886cb53356c",
        "x": "170200",
        "y": "440700",
    },
    "4104_nominal": {
        "filename": "regis_hydro_4104_nominal.ascii.txt",
        "sha256": "9bbab4688d86aec9d62788de411a29ce86fbae9d6a0f247c831d15a722ff6560",
        "x": "169600",
        "y": "441500",
    },
}

_X_RE = re.compile(r"^(top|bottom|kh|kv|c)\.x,\s*([^,\s]+)\s*$")
_ROW_RE = re.compile(
    r'^(top|bottom|kh|kv|c)\.\1\[\1\.layer="([^"]+)"\]\[\1\.y=([^\]]+)\],\s*([^,\s]+)\s*$'
)


@dataclass(frozen=True)
class ParsedHydroColumn:
    dataset: str
    x: Decimal
    y: Decimal
    layers: tuple[str, ...]
    values: dict[str, dict[str, Decimal | None]]


def _decimal(token: str, *, context: str) -> Decimal:
    try:
        value = Decimal(token.strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric token for {context}: {token!r}") from exc
    if not value.is_finite():
        raise ValueError(f"Non-finite numeric token for {context}: {token!r}")
    return value


def parse_regis_hydro_ascii(
    payload: bytes | str,
    *,
    expected_layer_count: int = EXPECTED_LAYER_COUNT,
) -> ParsedHydroColumn:
    """Parse one qualified TNO REGIS DAP2 ASCII point-column response.

    Parsing is name-based, not block-order based. Only the exact raw token
    ``-9999`` is mapped to missing. No interpolation or physical interpretation
    is performed.
    """
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    dataset: str | None = None
    x_by_variable: dict[str, Decimal] = {}
    y_by_variable: dict[str, Decimal] = {}
    layer_order: dict[str, list[str]] = {variable: [] for variable in VARIABLES}
    values: dict[str, dict[str, Decimal | None]] = {variable: {} for variable in VARIABLES}

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("Dataset:"):
            if dataset is not None:
                raise ValueError(f"Duplicate dataset record at line {line_number}")
            dataset = line.split(":", 1)[1].strip()
            continue

        x_match = _X_RE.fullmatch(line)
        if x_match:
            variable, token = x_match.groups()
            if variable in x_by_variable:
                raise ValueError(f"Duplicate {variable}.x record at line {line_number}")
            x_by_variable[variable] = _decimal(token, context=f"{variable}.x")
            continue

        row_match = _ROW_RE.fullmatch(line)
        if row_match:
            variable, layer, y_token, value_token = row_match.groups()
            if layer in values[variable]:
                raise ValueError(f"Duplicate {variable}/{layer} record at line {line_number}")

            y_value = _decimal(y_token, context=f"{variable}.y")
            previous_y = y_by_variable.get(variable)
            if previous_y is None:
                y_by_variable[variable] = y_value
            elif previous_y != y_value:
                raise ValueError(
                    f"Y-coordinate drift within {variable}: {previous_y} != {y_value}"
                )

            if value_token == MISSING_SENTINEL:
                value: Decimal | None = None
            else:
                value = _decimal(value_token, context=f"{variable}/{layer}")

            layer_order[variable].append(layer)
            values[variable][layer] = value
            continue

        raise ValueError(f"Unexpected DAP2 ASCII record at line {line_number}: {line!r}")

    if dataset != "REGIS.nc":
        raise ValueError(f"Unexpected or missing dataset label: {dataset!r}")
    if set(x_by_variable) != set(VARIABLES):
        raise ValueError(f"Missing x-coordinate blocks: {sorted(set(VARIABLES) - set(x_by_variable))}")
    if set(y_by_variable) != set(VARIABLES):
        raise ValueError(f"Missing y-coordinate blocks: {sorted(set(VARIABLES) - set(y_by_variable))}")

    x_values = set(x_by_variable.values())
    y_values = set(y_by_variable.values())
    if len(x_values) != 1:
        raise ValueError(f"X-coordinate differs between variable blocks: {x_by_variable}")
    if len(y_values) != 1:
        raise ValueError(f"Y-coordinate differs between variable blocks: {y_by_variable}")

    reference_layers = tuple(layer_order[VARIABLES[0]])
    if len(reference_layers) != expected_layer_count:
        raise ValueError(
            f"Unexpected layer count: {len(reference_layers)}; expected {expected_layer_count}"
        )
    if len(set(reference_layers)) != len(reference_layers):
        raise ValueError("Duplicate layer labels in reference variable block")

    for variable in VARIABLES:
        order = tuple(layer_order[variable])
        if len(order) != expected_layer_count:
            raise ValueError(
                f"Unexpected {variable} layer count: {len(order)}; expected {expected_layer_count}"
            )
        if order != reference_layers:
            raise ValueError(f"Layer-order drift in {variable} block")
        if set(values[variable]) != set(reference_layers):
            raise ValueError(f"Layer membership drift in {variable} block")

    return ParsedHydroColumn(
        dataset=dataset,
        x=next(iter(x_values)),
        y=next(iter(y_values)),
        layers=reference_layers,
        values=values,
    )


def _json_value(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def parsed_column_to_dict(column: ParsedHydroColumn) -> dict:
    rows = []
    for layer in column.layers:
        rows.append(
            {
                "layer": layer,
                **{variable: _json_value(column.values[variable][layer]) for variable in VARIABLES},
            }
        )
    return {
        "dataset": column.dataset,
        "x": str(column.x),
        "y": str(column.y),
        "layer_count": len(column.layers),
        "present_counts": {
            variable: sum(column.values[variable][layer] is not None for layer in column.layers)
            for variable in VARIABLES
        },
        "layers": rows,
    }


def qualify_hydro_columns(
    raw_dir: str | Path,
    output_path: str | Path,
    *,
    qualified_columns: dict[str, dict[str, str]] | None = None,
    expected_layer_count: int = EXPECTED_LAYER_COUNT,
) -> dict:
    """Parse and qualify the fixed raw hydro-column evidence bundle."""
    source = Path(raw_dir)
    expected = qualified_columns or QUALIFIED_RAW_COLUMNS
    output_columns: dict[str, dict] = {}
    reference_layers: tuple[str, ...] | None = None

    for column_id, metadata in expected.items():
        raw_path = source / metadata["filename"]
        if not raw_path.is_file():
            raise ValueError(f"Missing qualified raw response for {column_id}: {raw_path}")
        raw = raw_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != metadata["sha256"]:
            raise ValueError(
                f"Raw SHA-256 drift for {column_id}: {digest}; expected {metadata['sha256']}"
            )

        parsed = parse_regis_hydro_ascii(raw, expected_layer_count=expected_layer_count)
        if str(parsed.x) != metadata["x"] or str(parsed.y) != metadata["y"]:
            raise ValueError(
                f"Coordinate drift for {column_id}: ({parsed.x}, {parsed.y}) != "
                f"({metadata['x']}, {metadata['y']})"
            )
        if reference_layers is None:
            reference_layers = parsed.layers
        elif parsed.layers != reference_layers:
            raise ValueError(f"Layer-label drift between qualified columns at {column_id}")

        rendered = parsed_column_to_dict(parsed)
        rendered["source"] = {
            "artifact_file": metadata["filename"],
            "sha256": digest,
        }
        output_columns[column_id] = rendered

    result = {
        "capability": "STAGE_B_REGIS_PARSED_HYDRO_COLUMNS",
        "dependencies": {
            "raw_acquisition_run": "35132969090",
            "raw_artifact_id": "10461739661",
            "raw_artifact_digest_sha256": "6d06a51036e23f7dbbe7ec3636b5998435d64f2872eebd8a0eb07b6eb71e2695",
            "coordinate_mapping_sha256": "58596e715f335563f8654bf99ba4dcee190f7668ed9d76e1aa1ae37b5fd3389a",
        },
        "missing_semantics": {
            "raw_missing_token": MISSING_SENTINEL,
            "parsed_representation": None,
            "rule": "only exact raw token -9999 is mapped to missing; no imputation or clipping",
        },
        "variables": list(VARIABLES),
        "layer_count": expected_layer_count,
        "columns": output_columns,
        "guardrails": {
            "raw_hashes_verified": True,
            "screen_to_unit_mapping_performed": False,
            "hydrogeological_interpretation_performed": False,
            "admission_decision_performed": False,
        },
        "qualification_boundary": (
            "Deterministic parsing of the three qualified raw top/bottom/kh/kv/c columns only. "
            "No screen mapping, hydrogeological interpretation or Stage-B admission."
        ),
    }
    Path(output_path).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
