from __future__ import annotations

import argparse
import json

from .regis_hydro_probe import acquire_regis_hydro_evidence


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire bounded raw REGIS hydrogeological pilot columns")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_regis_hydro_evidence(args.output_dir)
    print(json.dumps({"counts": manifest["counts"], "responses": manifest["responses"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
