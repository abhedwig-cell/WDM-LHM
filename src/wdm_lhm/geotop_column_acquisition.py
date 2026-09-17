from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
import hashlib
import json


GEOTOP_DATASET_URL = "https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc"
COLUMN_VARIABLES = ("strat", "lithok")
QUALIFIED_X_INDEX = 1586
QUALIFIED_Y_INDEX = 1092
QUALIFIED_Z_START = 0
QUALIFIED_Z_STOP = 312
QUALIFIED_MAPPING_DEPENDENCY = {
    "head": "e22babf0dfea9dead8301c50a6bd439400663826",
    "x_index_zero_based": QUALIFIED_X_INDEX,
    "y_index_zero_based": QUALIFIED_Y_INDEX,
    "z_index_range_inclusive": [QUALIFIED_Z_START, QUALIFIED_Z_STOP],
    "dimensions": {"x": 2646, "y": 2811, "z": 313},
    "coordinate_ascii_sha256": "de1d362c38b6b3e021955580ad024d764e0f9cb5edc637318b450b63c3ce0b1a",
    "das_sha256": "50026e3c4a77062af4349ce5d932628c97fb24572e2f4d8a332c58a59947c7dc",
}


def _constraint(variable: str) -> str:
    return (
        f"{variable}[{QUALIFIED_X_INDEX}:1:{QUALIFIED_X_INDEX}]"
        f"[{QUALIFIED_Y_INDEX}:1:{QUALIFIED_Y_INDEX}]"
        f"[{QUALIFIED_Z_START}:1:{QUALIFIED_Z_STOP}]"
    )


COLUMN_CONSTRAINT_EXPRESSION = ",".join(_constraint(variable) for variable in COLUMN_VARIABLES)


@dataclass(frozen=True)
class GeoTopColumnAcquisitionConfig:
    dataset_url: str = GEOTOP_DATASET_URL
    max_response_bytes: int = 256 * 1024
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-column-acquisition/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


def build_column_ascii_url(
    dataset_url: str = GEOTOP_DATASET_URL,
    *,
    variables: tuple[str, ...] = COLUMN_VARIABLES,
    x_index: int = QUALIFIED_X_INDEX,
    y_index: int = QUALIFIED_Y_INDEX,
    z_start: int = QUALIFIED_Z_START,
    z_stop: int = QUALIFIED_Z_STOP,
) -> str:
    if dataset_url != GEOTOP_DATASET_URL:
        raise ValueError(f"GeoTOP column acquisition is pinned to {GEOTOP_DATASET_URL}")
    if variables != COLUMN_VARIABLES:
        raise ValueError(f"GeoTOP column acquisition must request exactly {COLUMN_VARIABLES!r}")
    if x_index != QUALIFIED_X_INDEX or y_index != QUALIFIED_Y_INDEX:
        raise ValueError("GeoTOP column acquisition must use the qualified x/y indices only")
    if z_start != QUALIFIED_Z_START or z_stop != QUALIFIED_Z_STOP:
        raise ValueError("GeoTOP column acquisition must use the complete qualified z-index range")
    return f"{dataset_url}.ascii?{COLUMN_CONSTRAINT_EXPRESSION}"


class GeoTopColumnClient:
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
                raise ValueError(f"GeoTOP column response exceeds guardrail: > {max_bytes} bytes")
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
        raise ValueError("GeoTOP column response escaped fixed host")
    if parsed.path != "/opendap/hyrax/GeoTOP/geotop.nc.ascii":
        raise ValueError("GeoTOP column response path drift")
    if unquote(parsed.query) != COLUMN_CONSTRAINT_EXPRESSION:
        raise ValueError(f"GeoTOP column query drift: {parsed.query!r}")
    if parsed.fragment:
        raise ValueError("GeoTOP column response contains unexpected fragment")


def acquire_geotop_single_column(
    output_dir: str | Path,
    config: GeoTopColumnAcquisitionConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    """Acquire raw strat/lithok values for one qualified GeoTOP x/y column only.

    Gate 3A is acquisition-only. The raw DAP2 ASCII response is retained before
    its live response shape or class values are parsed. No code-to-geology
    translation, vertical correlation or Stage-B admission is performed here.
    """
    cfg = config or GeoTopColumnAcquisitionConfig()
    requested_url = build_column_ascii_url(cfg.dataset_url)
    client = GeoTopColumnClient(cfg.timeout_s, cfg.user_agent, get_transport)
    payload, headers, final_url = client.get(requested_url, max_bytes=cfg.max_response_bytes)

    if not payload:
        raise ValueError("GeoTOP column response is empty")
    if len(payload) > cfg.max_response_bytes:
        raise ValueError(f"GeoTOP column response exceeds guardrail: {len(payload)}")
    _validate_final_url(final_url)

    content_type = headers.get("content-type", "")
    if not content_type.lower().startswith("text/plain"):
        raise ValueError(f"Unexpected GeoTOP column content type: {content_type!r}")
    if payload.lstrip().startswith(b"Error {"):
        raise ValueError("GeoTOP column response is a DAP error document")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw_name = "geotop_single_column.ascii.txt"
    (out / raw_name).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    manifest = {
        "capability": "STAGE_B_GEOTOP_20774_SINGLE_COLUMN_ACQUISITION",
        "state": "RAW_SINGLE_COLUMN_ACQUIRED_NOT_PARSED",
        "config": cfg.as_dict(),
        "mapping_dependency": QUALIFIED_MAPPING_DEPENDENCY,
        "request": {
            "requested_url": requested_url,
            "final_url": final_url,
            "variables": list(COLUMN_VARIABLES),
            "constraint_expression": COLUMN_CONSTRAINT_EXPRESSION,
            "x_index_zero_based": QUALIFIED_X_INDEX,
            "y_index_zero_based": QUALIFIED_Y_INDEX,
            "z_index_range_inclusive": [QUALIFIED_Z_START, QUALIFIED_Z_STOP],
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
            "single_horizontal_column_only": True,
            "categorical_voxel_values_requested": True,
            "strat_requested": True,
            "lithok_requested": True,
            "probability_grids_requested": False,
            "uncertainty_grids_requested": False,
            "neighbour_columns_requested": False,
            "response_parsed": False,
            "class_codes_interpreted": False,
            "screen_correlation_performed": False,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_single_column_acquisition_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
