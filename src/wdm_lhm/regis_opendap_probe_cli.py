from __future__ import annotations

import argparse
import json

from .regis_opendap_probe import RegisOpendapProbeConfig, probe_regis_opendap


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover REGIS OPeNDAP dataset metadata without reading model values")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--root-url", default=RegisOpendapProbeConfig().root_url)
    parser.add_argument("--max-depth", type=int, default=RegisOpendapProbeConfig().max_depth)
    parser.add_argument("--max-pages", type=int, default=RegisOpendapProbeConfig().max_pages)
    args = parser.parse_args()

    manifest = probe_regis_opendap(
        args.output_dir,
        RegisOpendapProbeConfig(
            root_url=args.root_url,
            max_depth=args.max_depth,
            max_pages=args.max_pages,
        ),
    )
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
