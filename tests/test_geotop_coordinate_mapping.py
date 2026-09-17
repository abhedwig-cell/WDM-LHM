from decimal import Decimal

import pytest

from wdm_lhm.geotop_coordinate_mapping import (
    TARGET_RD,
    build_coordinate_mapping,
    map_target_to_lower_edge_axis,
    parse_coordinate_ascii,
    parse_axis_das_metadata,
    regular_spacing,
    verify_horizontal_crs,
)


def _axis_line(name: str, start: Decimal, step: Decimal, count: int) -> str:
    values = [start + step * index for index in range(count)]
    return name + ", " + ", ".join(format(value, "f") for value in values)


def _coordinate_text() -> str:
    return "\n".join([
        "Dataset: geotop.nc",
        _axis_line("x", Decimal("13600"), Decimal("100"), 2646),
        _axis_line("y", Decimal("338500"), Decimal("100"), 2811),
        _axis_line("z", Decimal("-50"), Decimal("0.5"), 313),
    ]) + "\n"


DAS = '''Attributes {
    x {
        String epsg "7415";
        String units "m";
        String standard_name "projection_x_coordinate";
        String actual_range "13600.0 278200.0";
    }
    y {
        String epsg "7415";
        String units "m";
        String standard_name "projection_y_coordinate";
        String actual_range "338500.0 619600.0";
    }
    z {
        String epsg "7415";
        String units "m";
        String positive "up";
        String reference "NAP";
        String actual_range "-50.0 106.5";
    }
}
'''


def test_live_shape_ascii_parser_and_spacing():
    axes = parse_coordinate_ascii(_coordinate_text())
    assert {name: len(values) for name, values in axes.items()} == {"x": 2646, "y": 2811, "z": 313}
    assert regular_spacing(axes["x"], axis="x") == Decimal("100")
    assert regular_spacing(axes["y"], axis="y") == Decimal("100")
    assert regular_spacing(axes["z"], axis="z") == Decimal("0.5")


def test_extra_axis_record_fails_closed():
    bad = _coordinate_text() + "strat, 1\n"
    with pytest.raises(ValueError, match="exactly three axis records"):
        parse_coordinate_ascii(bad)


def test_non_finite_axis_fails_closed():
    bad = _coordinate_text().replace("x, 13600,", "x, NaN,", 1)
    with pytest.raises(ValueError, match="non-finite"):
        parse_coordinate_ascii(bad)


def test_non_monotonic_axis_fails_closed():
    bad = _coordinate_text().replace("x, 13600, 13700,", "x, 13600, 13600,", 1)
    with pytest.raises(ValueError, match="strictly increasing"):
        parse_coordinate_ascii(bad)


def test_irregular_spacing_fails_closed():
    axes = parse_coordinate_ascii(_coordinate_text())
    values = list(axes["x"])
    values[2] = Decimal("13801")
    with pytest.raises(ValueError, match="not exactly regular"):
        regular_spacing(tuple(values), axis="x")


def test_das_metadata_and_crs_are_qualified():
    metadata = parse_axis_das_metadata(DAS)
    assert metadata["x"]["epsg"] == "7415"
    crs = verify_horizontal_crs()
    assert crs["horizontal_epsg"] == 28992
    assert crs["compound_crs_name"] == "Amersfoort / RD New + NAP height"


def test_target_mapping_is_deterministic_and_no_threshold_is_invented():
    result = build_coordinate_mapping(_coordinate_text(), DAS)
    x = result["horizontal_mapping"]["x"]
    y = result["horizontal_mapping"]["y"]
    assert TARGET_RD == {"x": Decimal("172274.997571"), "y": Decimal("447781.978030")}
    assert x["index_zero_based"] == 1586
    assert x["lower_boundary"] == "172200"
    assert x["upper_boundary"] == "172300"
    assert x["distance_to_upper_boundary"] == "25.002429"
    assert y["index_zero_based"] == 1092
    assert y["lower_boundary"] == "447700"
    assert y["upper_boundary"] == "447800"
    assert y["distance_to_upper_boundary"] == "18.021970"
    assert result["boundary_sensitivity"]["minimum_horizontal_boundary_distance_m"] == "18.021970"
    assert result["boundary_sensitivity"]["generic_near_boundary_threshold_used"] is False


def test_exact_interior_boundary_is_not_silently_resolved():
    values = (Decimal("0"), Decimal("100"), Decimal("200"))
    with pytest.raises(ValueError, match="exactly on an interior"):
        map_target_to_lower_edge_axis(
            values,
            (Decimal("0"), Decimal("300")),
            Decimal("100"),
            axis="x",
        )


def test_actual_range_inconsistency_fails_closed():
    bad_das = DAS.replace('String actual_range "13600.0 278200.0";', 'String actual_range "13600.0 278100.0";')
    with pytest.raises(ValueError, match="actual_range is inconsistent"):
        build_coordinate_mapping(_coordinate_text(), bad_das)
