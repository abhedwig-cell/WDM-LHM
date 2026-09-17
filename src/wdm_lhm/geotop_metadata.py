from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re


GEOTOP_DATASET_URL = "https://www.dinodata.nl/opendap/hyrax/GeoTOP/geotop.nc"
_ALLOWED_SUFFIXES = (".dds", ".das")
_DDS_VAR = re.compile(
    r"^\s*(Byte|Int16|UInt16|Int32|UInt32|Float32|Float64|String)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)\s*((?:\[[^\]]+\])+?)\s*;\s*$"
)
_DDS_DIM = re.compile(r"\[\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\s*\]")


@dataclass(frozen=True)
class GeoTopMetadataConfig:
    dataset_url: str = GEOTOP_DATASET_URL
    max_metadata_bytes: int = 2_000_000
    timeout_s: int = 60
    user_agent: str = "wdm-lhm-geotop-metadata/0.8 (+research; public TNO DINOloket service)"

    def as_dict(self) -> dict:
        return asdict(self)


class GeoTopMetadataClient:
    def __init__(
        self,
        timeout_s: int = 60,
        user_agent: str = GeoTopMetadataConfig().user_agent,
        get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.get_transport = get_transport or self._get

    @staticmethod
    def _get(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        req = Request(url, headers=headers, method="GET")
        with urlopen(req, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"GeoTOP metadata response exceeds guardrail: > {max_bytes} bytes")
            return payload, {k.lower(): v for k, v in response.headers.items()}, response.geturl()

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str]:
        return self.get_transport(
            url,
            {"User-Agent": self.user_agent, "Accept": "text/plain,*/*"},
            self.timeout_s,
            max_bytes,
        )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_dataset_url(dataset_url: str) -> None:
    parsed = urlparse(dataset_url)
    if parsed.scheme != "https" or parsed.netloc != "www.dinodata.nl":
        raise ValueError("GeoTOP dataset host/scheme drift")
    if parsed.path != "/opendap/hyrax/GeoTOP/geotop.nc" or parsed.query or parsed.fragment:
        raise ValueError("GeoTOP dataset path drift")


def _validate_final_url(requested_url: str, final_url: str) -> None:
    req = urlparse(requested_url)
    final = urlparse(final_url)
    if final.scheme != "https" or final.netloc != "www.dinodata.nl":
        raise ValueError("GeoTOP metadata redirect escaped fixed host")
    if final.path != req.path or final.query or final.fragment:
        raise ValueError("GeoTOP metadata redirect changed fixed dataset resource")


def parse_dds(text: str) -> dict:
    if not text.strip().startswith("Dataset {") or not text.rstrip().endswith("geotop;"):
        raise ValueError("GeoTOP DDS does not have expected Dataset envelope")

    variables: dict[str, dict] = {}
    dimensions: dict[str, int] = {}
    for line in text.splitlines():
        match = _DDS_VAR.match(line)
        if not match:
            continue
        dtype, name, dims_text = match.groups()
        if name in variables:
            raise ValueError(f"duplicate DDS variable: {name}")
        dims: list[dict] = []
        for dim_name, size_text in _DDS_DIM.findall(dims_text):
            size = int(size_text)
            if size <= 0:
                raise ValueError(f"non-positive DDS dimension: {dim_name}={size}")
            previous = dimensions.get(dim_name)
            if previous is not None and previous != size:
                raise ValueError(f"inconsistent DDS dimension: {dim_name} {previous} != {size}")
            dimensions[dim_name] = size
            dims.append({"name": dim_name, "size": size})
        if not dims:
            raise ValueError(f"DDS variable without parsed dimensions: {name}")
        variables[name] = {"type": dtype, "dimensions": dims}

    for coordinate in ("x", "y", "z"):
        if coordinate not in variables:
            raise ValueError(f"required GeoTOP coordinate variable missing from DDS: {coordinate}")
        dims = variables[coordinate]["dimensions"]
        if len(dims) != 1 or dims[0]["name"] != coordinate:
            raise ValueError(f"GeoTOP coordinate variable {coordinate} is not one-dimensional on itself")

    return {"dimensions": dimensions, "variables": variables}


def validate_das(text: str) -> dict:
    stripped = text.strip()
    if not stripped.startswith("Attributes {") or not stripped.endswith("}"):
        raise ValueError("GeoTOP DAS does not have expected Attributes envelope")
    sections = sorted(set(re.findall(r"(?m)^\s{2}([A-Za-z_][A-Za-z0-9_]*)\s*\{", text)))
    if not sections:
        raise ValueError("GeoTOP DAS contains no attribute sections")
    return {"attribute_sections": sections}


def acquire_geotop_metadata(
    output_dir: str | Path,
    config: GeoTopMetadataConfig | None = None,
    *,
    get_transport: Callable[[str, dict[str, str], int, int], tuple[bytes, dict[str, str], str]] | None = None,
) -> dict:
    cfg = config or GeoTopMetadataConfig()
    _validate_dataset_url(cfg.dataset_url)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    client = GeoTopMetadataClient(cfg.timeout_s, cfg.user_agent, get_transport)

    records: dict[str, dict] = {}
    raw_text: dict[str, str] = {}
    for suffix in _ALLOWED_SUFFIXES:
        url = f"{cfg.dataset_url}{suffix}"
        payload, headers, final_url = client.get(url, max_bytes=cfg.max_metadata_bytes)
        _validate_final_url(url, final_url)
        if not payload:
            raise ValueError(f"empty GeoTOP metadata response: {suffix}")
        text = payload.decode("utf-8", errors="strict")
        raw_text[suffix] = text
        filename = f"geotop{suffix}.txt"
        (out / filename).write_bytes(payload)
        records[suffix[1:]] = {
            "requested_url": url,
            "final_url": final_url,
            "bytes": len(payload),
            "sha256": _sha256(payload),
            "content_type": headers.get("content-type"),
            "artifact_file": filename,
        }

    dds_inventory = parse_dds(raw_text[".dds"])
    das_inventory = validate_das(raw_text[".das"])
    variables = dds_inventory["variables"]

    manifest = {
        "capability": "STAGE_B_GEOTOP_20774_METADATA",
        "state": "METADATA_ACQUIRED_NOT_INTERPRETED",
        "config": cfg.as_dict(),
        "dataset": records,
        "dds_inventory": dds_inventory,
        "das_inventory": das_inventory,
        "expected_variable_presence": {
            "x": "x" in variables,
            "y": "y" in variables,
            "z": "z" in variables,
            "strat": "strat" in variables,
            "lithok": "lithok" in variables,
        },
        "guardrails": {
            "metadata_only": True,
            "data_requests_issued": False,
            "constraint_expression_issued": False,
            "voxel_values_read": False,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "screen_correlation_performed": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
    }
    (out / "geotop_metadata_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
