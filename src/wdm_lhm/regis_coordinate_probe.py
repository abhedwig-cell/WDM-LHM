from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import hashlib
import json


REGIS_DATASET_URL = "https://www.dinodata.nl/opendap/REGIS/REGIS.nc"
COORDINATE_VARIABLES = ("x", "y", "x_bounds", "y_bounds", "layer")


@dataclass(frozen=True)
class RegisCoordinateProbeConfig:
    dataset_url: str = REGIS_DATASET_URL
    max_response_bytes: int = 2 * 1024 * 1024
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-regis-coordinate-probe/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


def build_coordinate_ascii_url(
    dataset_url: str = REGIS_DATASET_URL,
    variables: tuple[str, ...] = COORDINATE_VARIABLES,
) -> str:
    if dataset_url != REGIS_DATASET_URL:
        raise ValueError(f"Coordinate acquisition is pinned to the qualified REGIS dataset: {dataset_url}")
    if variables != COORDINATE_VARIABLES:
        raise ValueError(f"Coordinate acquisition must request exactly {COORDINATE_VARIABLES!r}")
    return f"{dataset_url}.ascii?{','.join(variables)}"


class RegisCoordinateClient:
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
                raise ValueError(f"Coordinate response exceeds guardrail: > {max_bytes} bytes")
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


def acquire_regis_coordinate_evidence(
    output_dir: str | Path,
    config: RegisCoordinateProbeConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire only REGIS grid coordinates/layer labels as raw DAP2 ASCII evidence.

    This deliberately does not parse or request hydrogeological model variables.
    The raw coordinate response is retained so its exact server format can be
    inspected and qualified before deterministic point-to-cell lookup is coded.
    """
    cfg = config or RegisCoordinateProbeConfig()
    requested_url = build_coordinate_ascii_url(cfg.dataset_url)
    client = RegisCoordinateClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_response_bytes)

    if not payload:
        raise ValueError("Coordinate response is empty")
    if len(payload) > cfg.max_response_bytes:
        raise ValueError(f"Coordinate response exceeds guardrail: {len(payload)} > {cfg.max_response_bytes}")
    if not _same_fixed_ascii_endpoint(final_url):
        raise ValueError(f"Unexpected coordinate response endpoint: {final_url}")
    content_type = headers.get("content-type", "")
    if not content_type.lower().startswith("text/plain"):
        raise ValueError(f"Unexpected coordinate content type: {content_type!r}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "regis_coordinate_response.ascii.txt"
    raw_path = out / raw_name
    raw_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    manifest = {
        "capability": "STAGE_B_REGIS_COORDINATE_ACQUISITION",
        "config": cfg.as_dict(),
        "dataset_identity_dependency": {
            "version": "REGIS v02r2s3",
            "crs": "EPSG:28992",
            "qualified_dds_sha256": "298867cee98c3811a925aa47614d67484336f402b8a58bed492020cb4dfbd3af",
            "qualified_das_sha256": "1c14a662273eb0d30c945cee6030ae1a7bd7d484baeef09cd56dd8d06f25a173",
        },
        "request": {
            "requested_url": requested_url,
            "final_url": final_url,
            "variables": list(COORDINATE_VARIABLES),
        },
        "response": {
            "artifact_file": raw_name,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": content_type,
            "content_length": headers.get("content-length"),
            "last_modified": headers.get("last-modified"),
        },
        "guardrails": {
            "coordinate_values_requested": True,
            "hydrogeological_model_values_requested": False,
            "freatic_surface_requested": False,
            "point_to_cell_mapping_performed": False,
            "hydrogeological_interpretation_performed": False,
            "admission_decision_performed": False,
        },
        "qualification_boundary": (
            "Raw coordinate arrays and layer labels only. No top/bottom/hydraulic values, point mapping, hydrogeological interpretation or Stage-B admission."
        ),
    }
    (out / "regis_coordinate_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
