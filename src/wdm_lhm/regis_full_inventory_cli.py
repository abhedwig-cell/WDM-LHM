from __future__ import annotations

import argparse
import json

from .regis_full_inventory import build_regis_model_inventory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory the nested REGIS model ZIP without extracting model members"
    )
    parser.add_argument("outer_zip")
    parser.add_argument("output")
    parser.add_argument("--model-member")
    parser.add_argument(
        "--retain-inner-zip",
        action="store_true",
        help="Retain the extracted nested model ZIP for controlled debugging only",
    )
    args = parser.parse_args()

    result = build_regis_model_inventory(
        args.outer_zip,
        args.output,
        model_member=args.model_member,
        retain_inner_zip=args.retain_inner_zip,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
