from __future__ import annotations

import argparse
import json

from .geotop_current_delivery_page_acquisition import acquire_geotop_current_delivery_page


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Acquire one qualified official GeoTOP current-delivery page and inventory links only."
    )
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_current_delivery_page(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "final_url": manifest["request"]["final_url"],
        "sha256": manifest["response"]["sha256"],
        "marker_hits": manifest["marker_hits"],
        "candidate_authority_links": manifest["candidate_authority_links"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
