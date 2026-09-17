from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import hashlib
import json


REGIS_DATASET_URL = "https://www.dinodata.nl/opendap/REGIS/REGIS.nc"
HYDRO_VARIABLES = ("top", "bottom", "kh", "kv", "c")
LAYER_SLICE = "0:1:131"

POINT_COLUMNS = {
    "4074_nominal": {"gmw": "GMW000000004074", "x_index": 1703, "y_index": 1407},
    "4074_west_boundary_sensitivity": {
        "gmw": "GMW000000004074",
        "x_index": 1702,
        "y_index": 1407,
    },
    "4104_nominal": {"gmw": "GMW000000004104", "x_index": 1696, "y_index": 1415},
}

FORBIDDEN_INDEPENDENT_VARIABLES = ("freatisch", "kD", "hgv", "sdh", "sdv")


@dataclass(frozen=True)
class RegisHydroProbeConfig:
    dataset_url: str = REGIS_DATASET_URL
    max_response_bytes_per_column: int = 512 * 1024
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-regis-hydro-probe/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


def _projection(variable: str, *, x_index: int, y_index: int) -> str:
    return (
        f"{variable}[{LAYER_SLICE}]"
        f"[{y_index}:1:{y_index}]"
        f"[{x_index}:1:{x_index}]"
    )


def build_hydro_ascii_url(
    column_id: str,
    *,
    dataset_url: str = REGIS_DATASET_URL,
    variables: tuple[str, ...] = HYDRO_VARIABLES,
) -> str:
    if dataset_url != REGIS_DATASET_URL:
        raise ValueError(f"Hydro acquisition is pinned to the qualified REGIS dataset: {dataset_url}")
    if column_id not in POINT_COLUMNS:
        raise ValueError(f"Unknown qualified point column: {column_id}")
    if variables != HYDRO_VARIABLES:
        raise ValueError(f"Hydro acquisition must request exactly {HYDRO_VARIABLES!r}")
    if any(name in variables for name in FORBIDDEN_INDEPENDENT_VARIABLES):
        raise ValueError("Lineage-coupled or out-of-scope variable requested")

    point = POINT_COLUMNS[column_id]
    projections = [
        _projection(variable, x_index=point["x_index"], y_index=point["y_index"])
        for variable in variables
    ]
    return f"{dataset_url}.ascii?{','.join(projections)}"


class RegisHydroClient:
    def __init__(
        self,
        timeout_s: int,
        user_agent: str,
        get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get

    @staticmethod
    def _get(
        url: str,
        headers: dict[str, str],
        timeout_s: int,
        max_bytes: int,
    ) -> tuple[bytes, dict[str, str], str]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"Hydro response exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/plain,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _same_fixed_ascii_endpoint(final_url: str) -> bool:
    parsed = urlparse(final_url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "www.dinodata.nl"
        and parsed.path == "/opendap/REGIS/REGIS.nc.ascii"
    )


def acquire_regis_hydro_evidence(
    output_dir: str | Path,
    config: RegisHydroProbeConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire raw point-column values for the fixed Stage-B pilot cells only.

    The acquisition is deliberately interpretation-free. It excludes the REGIS
    freatic surface and kD because their lineage is not independent of LHM for
    the intended validation use.
    """
    cfg = config or RegisHydroProbeConfig()
    client = RegisHydroClient(cfg.timeout_s, cfg.user_agent, get_transport)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    responses: list[dict] = []
    total_bytes = 0
    for column_id, point in POINT_COLUMNS.items():
        requested_url = build_hydro_ascii_url(column_id, dataset_url=cfg.dataset_url)
        payload, headers, final_url = client.get(
            requested_url,
            max_bytes=cfg.max_response_bytes_per_column,
        )
        if not payload:
            raise ValueError(f"Hydro response is empty for {column_id}")
        if len(payload) > cfg.max_response_bytes_per_column:
            raise ValueError(
                f"Hydro response exceeds guardrail for {column_id}: "
                f"{len(payload)} > {cfg.max_response_bytes_per_column} bytes"
            )
        if not _same_fixed_ascii_endpoint(final_url):
            raise ValueError(f"Unexpected hydro response endpoint for {column_id}: {final_url}")
        content_type = headers.get("content-type", "")
        if not content_type.lower().startswith("text/plain"):
            raise ValueError(f"Unexpected hydro content type for {column_id}: {content_type!r}")

        digest = hashlib.sha256(payload).hexdigest()
        filename = f"regis_hydro_{column_id}.ascii.txt"
        (out / filename).write_bytes(payload)
        total_bytes += len(payload)
        responses.append(
            {
                "column_id": column_id,
                "gmw": point["gmw"],
                "x_index": point["x_index"],
                "y_index": point["y_index"],
                "requested_url": requested_url,
                "final_url": final_url,
                "variables": list(HYDRO_VARIABLES),
                "layer_slice": LAYER_SLICE,
                "artifact_file": filename,
                "bytes": len(payload),
                "sha256": digest,
                "content_type": content_type,
                "content_length": headers.get("content-length"),
                "last_modified": headers.get("last-modified"),
            }
        )

    manifest = {
        "capability": "STAGE_B_REGIS_RAW_HYDRO_COLUMNS",
        "config": cfg.as_dict(),
        "dependencies": {
            "version": "REGIS v02r2s3",
            "crs": "EPSG:28992",
            "qualified_coordinate_sha256": "fa39271a98fefa2091483b7247d53e3744e1e26e478969310ce6f3560725c7f3",
            "qualified_mapping_sha256": "58596e715f335563f8654bf99ba4dcee190f7668ed9d76e1aa1ae37b5fd3389a",
            "coordinate_checkpoint_head": "4727b1efe09c6ed31a723822b034b4caf5e2f1f3",
        },
        "responses": responses,
        "counts": {"columns": len(responses), "response_bytes": total_bytes},
        "guardrails": {
            "hydrogeological_model_values_requested": True,
            "freatic_surface_requested": False,
            "kd_requested": False,
            "screen_to_unit_mapping_performed": False,
            "hydrogeological_interpretation_performed": False,
            "admission_decision_performed": False,
        },
        "qualification_boundary": (
            "Raw top/bottom/kh/kv/c values for three fixed pilot columns only. "
            "No screen mapping, hydrogeological interpretation or Stage-B admission."
        ),
    }
    (out / "regis_hydro_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
