from __future__ import annotations

import argparse
import json

from .remote_zip import RemoteZipIndexConfig, index_remote_zip


def main() -> None:
    parser = argparse.ArgumentParser(description="Index a remote ZIP using HTTP byte ranges without downloading the archive")
    parser.add_argument("url")
    parser.add_argument("output")
    parser.add_argument("--timeout-s", type=int, default=60)
    parser.add_argument("--max-central-directory-mb", type=float, default=50.0)
    args = parser.parse_args()

    result = index_remote_zip(
        args.url,
        args.output,
        RemoteZipIndexConfig(
            timeout_s=args.timeout_s,
            max_central_directory_bytes=int(args.max_central_directory_mb * 1024 * 1024),
        ),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
