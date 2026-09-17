from __future__ import annotations

import argparse
import json

from .geotop_model_files_page_acquisition import acquire_geotop_model_files_page


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the official GeoTOP model-files page without submitting forms.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    m = acquire_geotop_model_files_page(args.output_dir)
    print(json.dumps({
        "capability": m["capability"],
        "state": m["state"],
        "final_url": m["request"]["final_url"],
        "sha256": m["response"]["sha256"],
        "marker_hits": m["marker_hits"],
        "candidate_authority_links": m["candidate_authority_links"],
        "forms": m["forms"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
