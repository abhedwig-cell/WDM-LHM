from __future__ import annotations

import argparse
import json

from .geotop_coordinate_mapping import qualify_coordinate_mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify GeoTOP coordinate semantics and map GMW 20774")
    parser.add_argument("--coordinate-file", required=True)
    parser.add_argument("--das-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    manifest = qualify_coordinate_mapping(
        args.coordinate_file,
        args.das_file,
        args.output_file,
    )
    mapping = manifest["mapping"]
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "x_index": mapping["horizontal_mapping"]["x"]["index_zero_based"],
        "y_index": mapping["horizontal_mapping"]["y"]["index_zero_based"],
        "minimum_boundary_distance_m": mapping["boundary_sensitivity"]["minimum_horizontal_boundary_distance_m"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
