from __future__ import annotations

import argparse
import json

from .regis_document_authority import extract_regis_authority_document


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the exact REGIS II v2.2.3 authority PDF from the qualified nested delivery"
    )
    parser.add_argument("outer_zip")
    parser.add_argument("output")
    parser.add_argument("--max-document-mib", type=float, default=5.0)
    args = parser.parse_args()

    manifest = extract_regis_authority_document(
        args.outer_zip,
        args.output,
        max_document_bytes=int(args.max_document_mib * 1024**2),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
