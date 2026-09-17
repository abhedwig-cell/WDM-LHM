from __future__ import annotations

import argparse
import json

from .geotop_column_acquisition import acquire_geotop_single_column


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire one raw GeoTOP strat/lithok column only")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_single_column(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "bytes": manifest["response"]["bytes"],
        "sha256": manifest["response"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
