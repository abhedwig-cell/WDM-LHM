from __future__ import annotations

import argparse
import json

from .geotop_authority_text_extraction import extract_geotop_authority_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify qualified GeoTOP authority PDFs and extract text without semantic translation."
    )
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = extract_geotop_authority_text(args.source_dir, args.output_dir)
    print(
        json.dumps(
            {
                "capability": manifest["capability"],
                "state": manifest["state"],
                "extractor_identity": manifest["extractor_identity"],
                "documents": {
                    key: {
                        "source_sha256": record["source_sha256"],
                        "text_sha256": record["text_sha256"],
                        "text_bytes": record["text_bytes"],
                        "marker_hits": record["marker_hits"],
                        "observed_code_occurrences": record["observed_code_occurrences"],
                    }
                    for key, record in manifest["documents"].items()
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
