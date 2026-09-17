from __future__ import annotations

import argparse
import json

from .regis_coordinate_probe import acquire_regis_coordinate_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire raw REGIS coordinate arrays only")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_regis_coordinate_evidence(args.output_dir)
    print(json.dumps({"request": manifest["request"], "response": manifest["response"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
