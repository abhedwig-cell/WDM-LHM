from __future__ import annotations

import argparse
import json

from .geotop_coordinate_acquisition import acquire_geotop_coordinate_axes


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire raw GeoTOP x/y/z coordinate axes only")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_coordinate_axes(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "bytes": manifest["response"]["bytes"],
        "sha256": manifest["response"]["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
