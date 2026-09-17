from __future__ import annotations

import argparse

from .regis_positive_case_20774 import (
    acquire_positive_case_columns,
    build_positive_case_geometry_context,
    parse_positive_case_columns,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded REGIS context for Stage-B positive case 20774")
    sub = parser.add_subparsers(dest="command", required=True)

    acquire = sub.add_parser("acquire")
    acquire.add_argument("--output-dir", required=True)

    parse = sub.add_parser("parse")
    parse.add_argument("--raw-dir", required=True)
    parse.add_argument("--manifest", required=True)
    parse.add_argument("--output", required=True)

    geometry = sub.add_parser("geometry")
    geometry.add_argument("--parsed", required=True)
    geometry.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "acquire":
        acquire_positive_case_columns(args.output_dir)
    elif args.command == "parse":
        parse_positive_case_columns(args.raw_dir, args.manifest, args.output)
    elif args.command == "geometry":
        build_positive_case_geometry_context(args.parsed, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
