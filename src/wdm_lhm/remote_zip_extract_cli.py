from __future__ import annotations

import argparse
import json
from pathlib import Path

from .remote_zip_extract import extract_remote_zip_member


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract one bounded member from a remote ZIP by HTTP byte ranges")
    parser.add_argument("url")
    parser.add_argument("index_json")
    parser.add_argument("member_name")
    parser.add_argument("output")
    parser.add_argument("--max-uncompressed-mb", type=float, default=10.0)
    args = parser.parse_args()

    index = json.loads(Path(args.index_json).read_text(encoding="utf-8"))
    matches = [e for e in index.get("entries", []) if e.get("name") == args.member_name]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one member named {args.member_name!r}; found {len(matches)}")
    out = extract_remote_zip_member(
        args.url,
        matches[0],
        args.output,
        max_uncompressed_bytes=int(args.max_uncompressed_mb * 1024 * 1024),
    )
    print(out)


if __name__ == "__main__":
    main()
