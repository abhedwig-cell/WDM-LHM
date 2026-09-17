from __future__ import annotations

import argparse
import json

from .regis_grid_mapping import qualify_coordinate_mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify REGIS coordinate parsing and target-to-cell mapping")
    parser.add_argument("--raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    mapping = qualify_coordinate_mapping(args.raw, args.output)
    print(json.dumps({"dimensions": mapping["dimensions"], "targets": mapping["targets"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
