from __future__ import annotations

import argparse
import json

from .geotop_reference_page_acquisition import acquire_geotop_reference_page


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire exact official GeoTOP dataset reference page only")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_reference_page(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "final_url": manifest["request"]["final_url"],
        "marker_hits": manifest["marker_hits"],
        "official_link_count": len(manifest["official_links"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
