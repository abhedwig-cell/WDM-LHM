from __future__ import annotations

import argparse
import json

from .regis_hydro_parse import qualify_hydro_columns


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse qualified raw REGIS hydro columns")
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = qualify_hydro_columns(args.raw_dir, args.output)
    print(
        json.dumps(
            {
                "layer_count": result["layer_count"],
                "columns": {
                    key: {
                        "x": value["x"],
                        "y": value["y"],
                        "present_counts": value["present_counts"],
                    }
                    for key, value in result["columns"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
