from __future__ import annotations

import argparse
import json

from .regis_screen_overlap import qualify_screen_overlap


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify BRO-screen to REGIS geometry overlap")
    parser.add_argument("--parsed", required=True, help="Qualified parsed REGIS hydro JSON")
    parser.add_argument("--output", required=True, help="Output overlap JSON")
    args = parser.parse_args()
    result = qualify_screen_overlap(args.parsed, args.output)
    print(json.dumps({
        "capability": result["capability"],
        "columns": sorted(result["results"]),
        "guardrails": result["guardrails"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
