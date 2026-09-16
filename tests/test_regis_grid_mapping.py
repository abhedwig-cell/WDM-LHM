from decimal import Decimal
from pathlib import Path
import hashlib

import pytest

from wdm_lhm.regis_grid_mapping import (
    RegisGrid,
    build_target_mapping,
    locate_axis,
    parse_regis_coordinate_ascii,
    qualify_coordinate_mapping,
)


def _small_payload() -> bytes:
    return b"\n".join(
        [
            b"Dataset: REGIS.nc",
            b"x, 0, 100, 200",
            b"y, 300000, 300100",
            b'layer, "A", "B"',
            b"x_bounds[0], 0, 100",
            b"x_bounds[1], 100, 200",
            b"x_bounds[2], 200, 300",
            b"y_bounds[0], 300000, 300100",
            b"y_bounds[1], 300100, 300200",
            b"",
        ]
    )


def test_parser_uses_explicit_bounds_and_preserves_layer_labels():
    grid = parse_regis_coordinate_ascii(_small_payload(), expected_x=3, expected_y=2, expected_layers=2)
    assert grid.dataset == "REGIS.nc"
    assert grid.x == (Decimal("0"), Decimal("100"), Decimal("200"))
    assert grid.x_bounds[1] == (Decimal("100"), Decimal("200"))
    assert grid.layers == ("A", "B")


def test_parser_fails_closed_on_gap_between_bounds():
    payload = _small_payload().replace(b"x, 0, 100, 200", b"x, 0, 100, 250").replace(
        b"x_bounds[2], 200, 300", b"x_bounds[2], 201, 300"
    )
    with pytest.raises(ValueError, match="not exactly contiguous"):
        parse_regis_coordinate_ascii(payload, expected_x=3, expected_y=2, expected_layers=2)


def test_exact_internal_boundary_is_ambiguous_not_silently_assigned():
    bounds = ((Decimal("0"), Decimal("100")), (Decimal("100"), Decimal("200")))
    location = locate_axis("100", bounds)
    assert location.status == "ON_INTERNAL_BOUNDARY"
    assert location.index is None
    assert location.candidate_indices == (0, 1)
    assert location.nearest_boundary_distance_m == "0"


def test_near_boundary_reports_distance_and_adjacent_cell_without_threshold():
    bounds = ((Decimal("170200"), Decimal("170300")), (Decimal("170300"), Decimal("170400")))
    location = locate_axis("170300.00558661332", bounds)
    assert location.status == "INSIDE_CELL"
    assert location.index == 1
    assert location.nearest_boundary_distance_m == "0.00558661332"
    assert location.adjacent_index_across_nearest_boundary == 0


def test_ts07_targets_resolve_from_explicit_regis_bounds():
    x_bounds = tuple((Decimal(i * 100), Decimal((i + 1) * 100)) for i in range(2800))
    y_bounds = tuple(
        (Decimal(300000 + i * 100), Decimal(300000 + (i + 1) * 100)) for i in range(3250)
    )
    grid = RegisGrid(
        dataset="REGIS.nc",
        x=tuple(lower for lower, _ in x_bounds),
        y=tuple(lower for lower, _ in y_bounds),
        layers=tuple(f"L{i}" for i in range(132)),
        x_bounds=x_bounds,
        y_bounds=y_bounds,
    )
    targets = build_target_mapping(grid)

    p4074 = targets["GMW000000004074"]
    assert p4074["nominal_cell"] == {"x_index": 1703, "y_index": 1407}
    assert p4074["x"]["nearest_boundary_distance_m"] == "0.00558661332"
    assert p4074["x"]["adjacent_index_across_nearest_boundary"] == 1702

    p4104 = targets["GMW000000004104"]
    assert p4104["nominal_cell"] == {"x_index": 1696, "y_index": 1415}
    assert p4104["x"]["nearest_boundary_distance_m"] == "19.99912779132"
    assert p4104["y"]["nearest_boundary_distance_m"] == "20.01161113486"


def test_qualification_pins_raw_evidence_hash(tmp_path: Path):
    lines = ["Dataset: REGIS.nc"]
    lines.append("x, " + ", ".join(str(i * 100) for i in range(2800)))
    lines.append("y, " + ", ".join(str(300000 + i * 100) for i in range(3250)))
    lines.append("layer, " + ", ".join(f'"L{i}"' for i in range(132)))
    lines.extend(f"x_bounds[{i}], {i * 100}, {(i + 1) * 100}" for i in range(2800))
    lines.extend(
        f"y_bounds[{i}], {300000 + i * 100}, {300000 + (i + 1) * 100}" for i in range(3250)
    )
    raw = ("\n".join(lines) + "\n").encode()
    raw_path = tmp_path / "raw.txt"
    raw_path.write_bytes(raw)
    output = tmp_path / "mapping.json"
    digest = hashlib.sha256(raw).hexdigest()

    mapping = qualify_coordinate_mapping(raw_path, output, expected_sha256=digest)
    assert mapping["targets"]["GMW000000004074"]["nominal_cell"] == {
        "x_index": 1703,
        "y_index": 1407,
    }
    assert mapping["guardrails"]["hydrogeological_model_values_requested"] is False
    assert output.is_file()

    with pytest.raises(ValueError, match="SHA-256 drift"):
        qualify_coordinate_mapping(raw_path, tmp_path / "bad.json", expected_sha256="0" * 64)
