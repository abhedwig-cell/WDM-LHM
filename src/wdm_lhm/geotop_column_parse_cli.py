from __future__ import annotations

import argparse
import json

from .geotop_column_parse import parse_geotop_single_column


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse qualified raw GeoTOP single-column evidence without interpretation")
    parser.add_argument("--raw-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    result = parse_geotop_single_column(args.raw_file, args.output_file)
    print(json.dumps({
        "capability": result["capability"],
        "state": result["state"],
        "count": result["structural_summary"]["count"],
        "strat_missing_count": result["structural_summary"]["strat_missing_count"],
        "lithok_missing_count": result["structural_summary"]["lithok_missing_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
