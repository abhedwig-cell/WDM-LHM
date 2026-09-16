from __future__ import annotations

import argparse
import json

from .regis_probe import RegisProbeConfig, probe_regis_delivery


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the public PDOK REGIS II ATOM delivery without downloading archives")
    parser.add_argument("output")
    parser.add_argument("--atom-url", default=RegisProbeConfig().atom_url)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--timeout-s", type=int, default=60)
    args = parser.parse_args()

    manifest = probe_regis_delivery(
        args.output,
        RegisProbeConfig(atom_url=args.atom_url, max_depth=args.max_depth, timeout_s=args.timeout_s),
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
