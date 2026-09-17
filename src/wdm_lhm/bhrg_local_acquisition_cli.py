from __future__ import annotations

import argparse
import json

from .bhrg_local_acquisition import acquire_local_bhrg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire bounded local BRO BHR-G raw evidence for GMW000000020774"
    )
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = acquire_local_bhrg(args.output_dir)
    print(json.dumps({
        "capability": manifest["capability"],
        "state": manifest["result"]["state"],
        "count": manifest["result"]["count"],
        "bro_ids": manifest["result"]["bro_ids"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
