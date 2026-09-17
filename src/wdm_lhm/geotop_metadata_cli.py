from __future__ import annotations

import argparse
import json

from .geotop_metadata import acquire_geotop_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire bounded GeoTOP DDS/DAS metadata only")
    parser.add_argument("--output-dir", default="stage_b_geotop_20774_metadata")
    args = parser.parse_args()
    manifest = acquire_geotop_metadata(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "dimensions": manifest["dds_inventory"]["dimensions"],
        "expected_variable_presence": manifest["expected_variable_presence"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
