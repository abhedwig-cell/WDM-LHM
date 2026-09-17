from __future__ import annotations

import argparse
import json

from .geotop_codebook_authority_discovery import acquire_geotop_authority_discovery


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire bounded official GeoTOP codebook-authority discovery resources")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_authority_discovery(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "official_link_count": len(manifest["official_links"]),
        "marker_hits": manifest["marker_hits"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
