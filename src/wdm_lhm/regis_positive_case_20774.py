from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json

from .regis_hydro_parse import parse_regis_hydro_ascii, parsed_column_to_dict
from .regis_hydro_probe import (
    HYDRO_VARIABLES,
    LAYER_SLICE,
    REGIS_DATASET_URL,
    RegisHydroClient,
    RegisHydroProbeConfig,
)

CASE_ID = "GMW000000020774_T1"
GROUND_LEVEL_M_NAP = Decimal("9.85")
Q95_DEPTH_M_BGL = Decimal("2.054")
SCREEN_TOP_M_NAP = Decimal("6.520")
SCREEN_BOTTOM_M_NAP = Decimal("5.520")
SUPPORT_BOTTOM_M_NAP = GROUND_LEVEL_M_NAP - Q95_DEPTH_M_BGL

TARGET_COLUMNS = {
    "20774_nominal": {"x_index": 1722, "y_index": 1477, "x": "172200", "y": "447700"},
    "20774_east": {"x_index": 1723, "y_index": 1477, "x": "172300", "y": "447700"},
    "20774_north": {"x_index": 1722, "y_index": 1478, "x": "172200", "y": "447800"},
    "20774_north_east": {"x_index": 1723, "y_index": 1478, "x": "172300", "y": "447800"},
}

FORBIDDEN_VARIABLES = ("freatisch", "kD", "hgv", "sdh", "sdv")


def _projection(variable: str, *, x_index: int, y_index: int) -> str:
    return (
        f"{variable}[{LAYER_SLICE}]"
        f"[{y_index}:1:{y_index}]"
        f"[{x_index}:1:{x_index}]"
    )


def build_positive_case_ascii_url(column_id: str) -> str:
    if column_id not in TARGET_COLUMNS:
        raise ValueError(f"Unknown positive-case column: {column_id}")
    if any(variable in HYDRO_VARIABLES for variable in FORBIDDEN_VARIABLES):
        raise ValueError("Forbidden lineage-coupled variable configured")
    point = TARGET_COLUMNS[column_id]
    projections = [
        _projection(variable, x_index=point["x_index"], y_index=point["y_index"])
        for variable in HYDRO_VARIABLES
    ]
    return f"{REGIS_DATASET_URL}.ascii?{','.join(projections)}"


def _same_fixed_ascii_endpoint(final_url: str) -> bool:
    parsed = urlparse(final_url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "www.dinodata.nl"
        and parsed.path == "/opendap/REGIS/REGIS.nc.ascii"
    )


def acquire_positive_case_columns(
    output_dir: str | Path,
    config: RegisHydroProbeConfig | None = None,
    *,
    get_transport=None,
) -> dict:
    cfg = config or RegisHydroProbeConfig()
    if cfg.dataset_url != REGIS_DATASET_URL:
        raise ValueError("Positive-case acquisition is pinned to the qualified REGIS dataset")

    client = RegisHydroClient(cfg.timeout_s, cfg.user_agent, get_transport)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    responses: list[dict] = []

    for column_id, point in TARGET_COLUMNS.items():
        requested_url = build_positive_case_ascii_url(column_id)
        payload, headers, final_url = client.get(
            requested_url,
            max_bytes=cfg.max_response_bytes_per_column,
        )
        if not payload:
            raise ValueError(f"Empty REGIS response for {column_id}")
        if not _same_fixed_ascii_endpoint(final_url):
            raise ValueError(f"Unexpected REGIS endpoint for {column_id}: {final_url}")
        content_type = headers.get("content-type", "")
        if not content_type.lower().startswith("text/plain"):
            raise ValueError(f"Unexpected content type for {column_id}: {content_type!r}")

        digest = hashlib.sha256(payload).hexdigest()
        filename = f"regis_positive_20774_{column_id}.ascii.txt"
        (out / filename).write_bytes(payload)
        responses.append(
            {
                "column_id": column_id,
                **point,
                "artifact_file": filename,
                "bytes": len(payload),
                "sha256": digest,
                "requested_url": requested_url,
                "final_url": final_url,
                "variables": list(HYDRO_VARIABLES),
                "content_type": content_type,
                "last_modified": headers.get("last-modified"),
            }
        )

    manifest = {
        "capability": "STAGE_B_POSITIVE_20774_REGIS_CONTEXT_ACQUISITION",
        "case_id": CASE_ID,
        "dataset": REGIS_DATASET_URL,
        "variables": list(HYDRO_VARIABLES),
        "responses": responses,
        "guardrails": {
            "fixed_four_columns_only": True,
            "columns_averaged": False,
            "freatic_surface_requested": False,
            "kd_requested": False,
            "hydraulic_semantics_applied": False,
            "admission_decision_performed": False,
        },
    }
    (out / "regis_positive_20774_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def parse_positive_case_columns(
    raw_dir: str | Path,
    manifest_path: str | Path,
    output_path: str | Path,
) -> dict:
    source = Path(raw_dir)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    responses = {item["column_id"]: item for item in manifest["responses"]}
    if set(responses) != set(TARGET_COLUMNS):
        raise ValueError("Positive-case raw column membership drift")

    columns: dict[str, dict] = {}
    reference_layers: tuple[str, ...] | None = None
    for column_id, target in TARGET_COLUMNS.items():
        response = responses[column_id]
        if response["variables"] != list(HYDRO_VARIABLES):
            raise ValueError(f"Variable drift for {column_id}")
        raw_path = source / response["artifact_file"]
        payload = raw_path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if digest != response["sha256"]:
            raise ValueError(f"Raw SHA drift for {column_id}")
        parsed = parse_regis_hydro_ascii(payload)
        if str(parsed.x) != target["x"] or str(parsed.y) != target["y"]:
            raise ValueError(
                f"Coordinate drift for {column_id}: ({parsed.x},{parsed.y}) != "
                f"({target['x']},{target['y']})"
            )
        if reference_layers is None:
            reference_layers = parsed.layers
        elif parsed.layers != reference_layers:
            raise ValueError(f"Layer label drift at {column_id}")
        rendered = parsed_column_to_dict(parsed)
        rendered["source"] = {"artifact_file": response["artifact_file"], "sha256": digest}
        columns[column_id] = rendered

    output = {
        "capability": "STAGE_B_POSITIVE_20774_REGIS_CONTEXT_PARSED",
        "case_id": CASE_ID,
        "variables": list(HYDRO_VARIABLES),
        "missing_semantics": {
            "raw_missing_token": "-9999",
            "parsed_representation": None,
            "imputation_performed": False,
        },
        "columns": columns,
        "guardrails": {
            "columns_averaged": False,
            "hydraulic_semantics_applied": False,
            "admission_decision_performed": False,
        },
    }
    Path(output_path).write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    return output


def _decimal(value: str, *, context: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal for {context}: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Non-finite decimal for {context}: {value!r}")
    return result


def _interval_layers(column: dict, *, top_m_nap: Decimal, bottom_m_nap: Decimal) -> list[dict]:
    if top_m_nap <= bottom_m_nap:
        raise ValueError("Interval top must be above interval bottom")
    rows: list[dict] = []
    for row in column["layers"]:
        if row["layer"] == "mv" or row.get("top") is None or row.get("bottom") is None:
            continue
        layer_top = _decimal(row["top"], context=f"{row['layer']}/top")
        layer_bottom = _decimal(row["bottom"], context=f"{row['layer']}/bottom")
        if layer_top < layer_bottom:
            raise ValueError(f"Inverted REGIS geometry for {row['layer']}")
        overlap = min(layer_top, top_m_nap) - max(layer_bottom, bottom_m_nap)
        if overlap <= 0:
            continue
        rows.append(
            {
                "layer": row["layer"],
                "layer_top_m_nap": str(layer_top),
                "layer_bottom_m_nap": str(layer_bottom),
                "overlap_m": str(overlap),
                "kh": row.get("kh"),
                "kv": row.get("kv"),
                "c": row.get("c"),
            }
        )
    return rows


def build_positive_case_geometry_context(
    parsed_path: str | Path,
    output_path: str | Path,
) -> dict:
    parsed = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    if set(parsed["columns"]) != set(TARGET_COLUMNS):
        raise ValueError("Positive-case parsed column membership drift")

    contexts: dict[str, dict] = {}
    sequences: dict[str, tuple[str, ...]] = {}
    for column_id, column in parsed["columns"].items():
        support_to_screen = _interval_layers(
            column,
            top_m_nap=SUPPORT_BOTTOM_M_NAP,
            bottom_m_nap=SCREEN_BOTTOM_M_NAP,
        )
        screen = _interval_layers(
            column,
            top_m_nap=SCREEN_TOP_M_NAP,
            bottom_m_nap=SCREEN_BOTTOM_M_NAP,
        )
        sequence = tuple(row["layer"] for row in support_to_screen)
        sequences[column_id] = sequence
        contexts[column_id] = {
            "support_to_screen_interval_m_nap": {
                "top": str(SUPPORT_BOTTOM_M_NAP),
                "bottom": str(SCREEN_BOTTOM_M_NAP),
            },
            "support_to_screen_layers": support_to_screen,
            "support_to_screen_layer_sequence": list(sequence),
            "screen_layers": screen,
            "screen_layer_sequence": [row["layer"] for row in screen],
        }

    unique_sequences = {sequence for sequence in sequences.values()}
    geometry_stable = len(unique_sequences) == 1
    output = {
        "capability": "STAGE_B_POSITIVE_20774_REGIS_GEOMETRY_CONTEXT",
        "case_id": CASE_ID,
        "direct_evidence": {
            "ground_level_m_nap": str(GROUND_LEVEL_M_NAP),
            "q95_depth_m_bgl": str(Q95_DEPTH_M_BGL),
            "q95_elevation_m_nap": str(SUPPORT_BOTTOM_M_NAP),
            "screen_top_m_nap": str(SCREEN_TOP_M_NAP),
            "screen_bottom_m_nap": str(SCREEN_BOTTOM_M_NAP),
        },
        "columns": contexts,
        "comparison": {
            "support_to_screen_geometry_same_sequence_all_columns": geometry_stable,
            "sequences": {key: list(value) for key, value in sequences.items()},
            "columns_averaged": False,
        },
        "scientific_boundary": {
            "regional_context_state": "UNKNOWN",
            "hydraulic_continuity_established": False,
            "reason": "GEOMETRY_AND_RAW_PROPERTIES_ONLY_NO_QUALIFIED_LOCAL_HYDRAULIC_SEMANTICS",
            "admissible_freatic_assigned": False,
        },
        "guardrails": {
            "layer_codes_not_interpreted_hydraulically": True,
            "kh_kv_c_not_thresholded": True,
            "freatic_surface_not_used": True,
            "kd_not_used": True,
            "columns_averaged": False,
        },
    }
    Path(output_path).write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    return output
