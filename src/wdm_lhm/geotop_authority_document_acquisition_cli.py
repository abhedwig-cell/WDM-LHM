from __future__ import annotations

import argparse
import json

from .geotop_authority_document_acquisition import acquire_geotop_authority_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire bounded official GeoTOP authority documents")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_geotop_authority_documents(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["state"],
        "documents": {k: {"sha256": v["sha256"], "bytes": v["bytes"]} for k, v in manifest["documents"].items()},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
