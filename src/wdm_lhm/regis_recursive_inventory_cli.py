from __future__ import annotations

import argparse
import json

from .regis_recursive_inventory import build_recursive_regis_inventory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recursively inventory nested REGIS ZIP containers without extracting non-ZIP model members"
    )
    parser.add_argument("outer_zip")
    parser.add_argument("output")
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--max-containers", type=int, default=32)
    parser.add_argument("--max-total-zip-gib", type=float, default=8.0)
    args = parser.parse_args()

    manifest = build_recursive_regis_inventory(
        args.outer_zip,
        args.output,
        max_depth=args.max_depth,
        max_containers=args.max_containers,
        max_total_materialized_zip_bytes=int(args.max_total_zip_gib * 1024**3),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
