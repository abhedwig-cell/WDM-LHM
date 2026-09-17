from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
import hashlib
import json


GEOTOP_DATASET_URL = "https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc"
COORDINATE_VARIABLES = ("x", "y", "z")
QUALIFIED_METADATA_DEPENDENCY = {
    "head": "099ea43a845179df70d811c7826a1a9badad355c",
    "dds_sha256": "845bf38ef3bcbed025e0a01925508f5f143644c188e9ff703651a85d8fe5ba07",
    "das_sha256": "50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc",
    "dimensions": {"x": 2646, "y": 2811, "z": 313},
}


@dataclass(frozen=True)
class GeoTopCoordinateAcquisitionConfig:
    dataset_url: str = GEOTOP_DATASET_URL
    max_response_bytes: int = 2 * 1024 * 1024
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-coordinate-acquisition/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


def build_coordinate_ascii_url(
    dataset_url: str = GEOTOP_DATASET_URL,
    variables: tuple[str, ...] = COORDINATE_VARIABLES,
) -> str:
    if dataset_url != GEOTOP_DATASET_URL:
        raise ValueError(f"GeoTOP coordinate acquisition is pinned to {GEOTOP_DATASET_URL}")
    if variables != COORDINATE_VARIABLES:
        raise ValueError(f"GeoTOP coordinate acquisition must request exactly {COORDINATE_VARIABLES!r}")
    return f"{dataset_url}.ascii?{','.join(variables)}"


class GeoTopCoordinateClient:
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
                raise ValueError(f"GeoTOP coordinate response exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/plain,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _validate_final_url(final_url: str) -> None:
    parsed = urlparse(final_url)
    if parsed.scheme != "https" or parsed.netloc != "www.dinodata.nl":
        raise ValueError("GeoTOP coordinate response escaped fixed host")
    if parsed.path != "/opendap/hyrax/GeoTOP/geotop.nc.ascii":
        raise ValueError("GeoTOP coordinate response path drift")
    if unquote(parsed.query) != "x,y,z":
        raise ValueError(f"GeoTOP coordinate query drift: {parsed.query!r}")
    if parsed.fragment:
        raise ValueError("GeoTOP coordinate response contains unexpected fragment")


def acquire_geotop_coordinate_axes(
    output_dir: str | Path,
    config: GeoTopCoordinateAcquisitionConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire raw GeoTOP x/y/z axes only.

    This is Gate 2A. It intentionally does not parse the live ASCII structure,
    map the target coordinate, request strat/lithok, or perform geological or
    hydraulic interpretation. The raw server response is retained first so the
    parser can be qualified against immutable live evidence in Gate 2B.
    """
    cfg = config or GeoTopCoordinateAcquisitionConfig()
    requested_url = build_coordinate_ascii_url(cfg.dataset_url)
    client = GeoTopCoordinateClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_response_bytes)

    if not payload:
        raise ValueError("GeoTOP coordinate response is empty")
    if len(payload) > cfg.max_response_bytes:
        raise ValueError(f"GeoTOP coordinate response exceeds guardrail: {len(payload)}")
    _validate_final_url(final_url)

    content_type = headers.get("content-type", "")
    if not content_type.lower().startswith("text/plain"):
        raise ValueError(f"Unexpected GeoTOP coordinate content type: {content_type!r}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "geotop_coordinate_axes.ascii.txt"
    (out / raw_name).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    manifest = {
        "capability": "STAGE_B_GEOTOP_20774_COORDINATE_ACQUISITION",
        "state": "RAW_COORDINATE_AXES_ACQUIRED_NOT_PARSED",
        "config": cfg.as_dict(),
        "metadata_dependency": QUALIFIED_METADATA_DEPENDENCY,
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
            "categorical_voxel_values_requested": False,
            "strat_requested": False,
            "lithok_requested": False,
            "coordinate_axes_parsed": False,
            "point_to_cell_mapping_performed": False,
            "screen_correlation_performed": False,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_coordinate_acquisition_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
