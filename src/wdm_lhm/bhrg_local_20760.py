from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .bhrg_local_acquisition import LocalBhrgConfig, Transport, acquire_local_bhrg


TARGET_GMW = "GMW000000020760"
TARGET_STATION = "GMW000000020760_T1"
TARGET_X_RD = 174493.0038178011
TARGET_Y_RD = 446332.9711833446
REQUEST_REFERENCE = "wdm-lhm-stage-b-local-bhrg-20760"
CAPABILITY = "STAGE_B_LOCAL_BHRG_20760_ACQUISITION"


def _config() -> LocalBhrgConfig:
    return LocalBhrgConfig(
        target_gmw=TARGET_GMW,
        target_station=TARGET_STATION,
        x_rd=TARGET_X_RD,
        y_rd=TARGET_Y_RD,
        request_reference=REQUEST_REFERENCE,
        user_agent="wdm-lhm-stage-b-local-bhrg-20760/0.9 (+research; public BRO service)",
    )


def acquire_local_bhrg_20760(
    output_dir: str | Path,
    *,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Reuse the qualified local BHR-G acquisition engine for 20760 only.

    The underlying engine remains unchanged. This adapter supplies the candidate
    coordinate/identity and rewrites only the candidate-specific manifest label
    and qualification boundary after acquisition.
    """

    out = Path(output_dir)
    manifest = acquire_local_bhrg(out, config=_config(), transport=transport)

    target = manifest.get("target", {})
    if target.get("gmw") != TARGET_GMW or target.get("station") != TARGET_STATION:
        raise ValueError(f"Unexpected BHR-G target returned by acquisition engine: {target}")

    manifest["capability"] = CAPABILITY
    manifest["qualification_boundary"] = (
        "Local BHR-G discovery and raw object acquisition for GMW000000020760 only. "
        "No material/lithological interpretation, screen correlation, hydraulic continuity "
        "inference or Stage-B admission."
    )
    manifest["adapter"] = {
        "reused_engine": "wdm_lhm.bhrg_local_acquisition.acquire_local_bhrg",
        "candidate_specific_network_logic_added": False,
        "manifest_candidate_label_rewritten": True,
    }

    (out / "bhrg_local_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Acquire bounded local BRO BHR-G raw evidence for GMW000000020760"
    )
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    manifest = acquire_local_bhrg_20760(args.output_dir)
    print(
        json.dumps(
            {
                "capability": manifest["capability"],
                "state": manifest["result"]["state"],
                "count": manifest["result"]["count"],
                "bro_ids": manifest["result"]["bro_ids"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
