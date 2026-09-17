from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import hashlib
import json
import re
import xml.etree.ElementTree as ET

from pyproj import Transformer


BHRG_BASE = "https://publiek.broservices.nl/sr/bhrg/v3"
TARGET_GMW = "GMW000000020774"
TARGET_STATION = "GMW000000020774_T1"
TARGET_X_RD = 172274.997571
TARGET_Y_RD = 447781.978030
SEARCH_RADIUS_KM = 0.5
MAX_RESULTS = 25
MAX_CHARACTERISTICS_BYTES = 2 * 1024 * 1024
MAX_OBJECT_BYTES = 8 * 1024 * 1024
REQUEST_REFERENCE = "wdm-lhm-stage-b-local-bhrg-20774"
_BRO_ID_RE = re.compile(r"^BHR[A-Za-z0-9]+$")


@dataclass(frozen=True)
class LocalBhrgConfig:
    base_url: str = BHRG_BASE
    target_gmw: str = TARGET_GMW
    target_station: str = TARGET_STATION
    x_rd: float = TARGET_X_RD
    y_rd: float = TARGET_Y_RD
    radius_km: float = SEARCH_RADIUS_KM
    max_results: int = MAX_RESULTS
    timeout_s: int = 60
    max_characteristics_bytes: int = MAX_CHARACTERISTICS_BYTES
    max_object_bytes: int = MAX_OBJECT_BYTES
    request_reference: str = REQUEST_REFERENCE
    user_agent: str = "wdm-lhm-stage-b-local-bhrg/0.9 (+research; public BRO service)"

    def as_dict(self) -> dict:
        return asdict(self)


Transport = Callable[
    [str, str, dict[str, str], bytes | None, int, int],
    tuple[bytes, dict[str, str], str, int],
]


def rd_to_wgs84(x_rd: float, y_rd: float) -> tuple[float, float]:
    transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x_rd, y_rd)
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError(f"Invalid transformed coordinate: lon={lon}, lat={lat}")
    return round(float(lon), 9), round(float(lat), 9)


def build_characteristics_url(
    *,
    base_url: str = BHRG_BASE,
    request_reference: str = REQUEST_REFERENCE,
) -> str:
    if base_url.rstrip("/") != BHRG_BASE:
        raise ValueError(f"BHR-G acquisition is pinned to {BHRG_BASE}")
    return f"{BHRG_BASE}/characteristics/searches?requestReference={quote(request_reference, safe='')}"


def build_characteristics_body(config: LocalBhrgConfig | None = None) -> dict:
    cfg = config or LocalBhrgConfig()
    if cfg.base_url.rstrip("/") != BHRG_BASE:
        raise ValueError(f"BHR-G acquisition is pinned to {BHRG_BASE}")
    if cfg.radius_km <= 0:
        raise ValueError("Search radius must be positive")
    lon, lat = rd_to_wgs84(cfg.x_rd, cfg.y_rd)
    return {
        "area": {
            "enclosingCircle": {
                "center": {"lat": lat, "lon": lon},
                "radius": cfg.radius_km,
            }
        }
    }


def build_object_url(bro_id: str, *, base_url: str = BHRG_BASE) -> str:
    if base_url.rstrip("/") != BHRG_BASE:
        raise ValueError(f"BHR-G acquisition is pinned to {BHRG_BASE}")
    if not _BRO_ID_RE.fullmatch(bro_id):
        raise ValueError(f"Unexpected BHR-G BRO-ID: {bro_id!r}")
    return f"{BHRG_BASE}/objects/{quote(bro_id, safe='')}"


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _number_of_documents(root: ET.Element) -> int | None:
    values: list[int] = []
    for elem in root.iter():
        for key, raw in elem.attrib.items():
            if _localname(key) == "numberOfDocuments":
                try:
                    values.append(int(raw))
                except ValueError as exc:
                    raise ValueError(f"Invalid numberOfDocuments: {raw!r}") from exc
    if not values:
        return None
    if len(set(values)) != 1:
        raise ValueError(f"Conflicting numberOfDocuments values: {values}")
    return values[0]


def parse_characteristics_response(payload: bytes | str, *, max_results: int = MAX_RESULTS) -> list[str]:
    if max_results < 0:
        raise ValueError("max_results must be non-negative")
    raw = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    if not raw.strip():
        raise ValueError("Empty BHR-G characteristics response")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("Malformed BHR-G characteristics XML") from exc

    response_types = [
        (elem.text or "").strip().lower()
        for elem in root.iter()
        if _localname(elem.tag) == "responseType" and (elem.text or "").strip()
    ]
    if response_types and any(value not in {"dispatch", "success"} for value in response_types):
        raise ValueError(f"BHR-G characteristics response is not a dispatch: {response_types}")

    bro_ids: list[str] = []
    for elem in root.iter():
        if _localname(elem.tag) != "broId":
            continue
        value = (elem.text or "").strip()
        if not value:
            continue
        if value.startswith("BHR"):
            if not _BRO_ID_RE.fullmatch(value):
                raise ValueError(f"Malformed BHR-G BRO-ID: {value!r}")
            bro_ids.append(value)

    if len(bro_ids) != len(set(bro_ids)):
        raise ValueError("Duplicate BHR-G BRO-ID in characteristics response")
    declared = _number_of_documents(root)
    if declared is not None and declared != len(bro_ids):
        raise ValueError(
            f"numberOfDocuments mismatch: declared {declared}, parsed {len(bro_ids)}"
        )
    if len(bro_ids) > max_results:
        raise ValueError(
            f"BHR-G result count exceeds bounded guardrail: {len(bro_ids)} > {max_results}"
        )
    return bro_ids


def _extract_bhr_ids(payload: bytes) -> set[str]:
    if not payload.strip():
        raise ValueError("Empty BHR-G object response")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError("Malformed BHR-G object XML") from exc
    ids: set[str] = set()
    for elem in root.iter():
        if _localname(elem.tag) != "broId":
            continue
        value = (elem.text or "").strip()
        if value.startswith("BHR"):
            ids.add(value)
    return ids


def _allowed_final_url(final_url: str, expected_url: str) -> bool:
    final = urlparse(final_url)
    expected = urlparse(expected_url)
    return (
        final.scheme == "https"
        and final.netloc == "publiek.broservices.nl"
        and final.path == expected.path
        and final.query == expected.query
    )


class BhrgClient:
    def __init__(
        self,
        *,
        timeout_s: int = 60,
        user_agent: str = LocalBhrgConfig().user_agent,
        transport: Transport | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.transport = transport or self._urllib_transport

    @staticmethod
    def _urllib_transport(
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | None,
        timeout_s: int,
        max_bytes: int,
    ) -> tuple[bytes, dict[str, str], str, int]:
        request = Request(url, data=body, headers=headers, method=method)
        with urlopen(request, timeout=timeout_s) as response:
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"BHR-G response exceeds guardrail: > {max_bytes} bytes")
            return (
                payload,
                {key.lower(): value for key, value in response.headers.items()},
                response.geturl(),
                int(response.status),
            )

    def post_json(self, url: str, body: dict, *, max_bytes: int) -> tuple[bytes, dict[str, str], str, int]:
        encoded = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self.transport(
            "POST",
            url,
            {
                "User-Agent": self.user_agent,
                "Accept": "application/xml,text/xml,*/*",
                "Content-Type": "application/json",
            },
            encoded,
            self.timeout_s,
            max_bytes,
        )

    def get(self, url: str, *, max_bytes: int) -> tuple[bytes, dict[str, str], str, int]:
        return self.transport(
            "GET",
            url,
            {"User-Agent": self.user_agent, "Accept": "application/xml,text/xml,*/*"},
            None,
            self.timeout_s,
            max_bytes,
        )


def acquire_local_bhrg(
    output_dir: str | Path,
    config: LocalBhrgConfig | None = None,
    *,
    transport: Transport | None = None,
) -> dict:
    cfg = config or LocalBhrgConfig()
    if cfg.base_url.rstrip("/") != BHRG_BASE:
        raise ValueError(f"BHR-G acquisition is pinned to {BHRG_BASE}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    client = BhrgClient(timeout_s=cfg.timeout_s, user_agent=cfg.user_agent, transport=transport)
    search_url = build_characteristics_url(
        base_url=cfg.base_url,
        request_reference=cfg.request_reference,
    )
    request_body = build_characteristics_body(cfg)
    request_bytes = json.dumps(request_body, indent=2, sort_keys=True).encode("utf-8")
    request_path = out / "bhrg_characteristics_request.json"
    request_path.write_bytes(request_bytes)

    payload, headers, final_url, status = client.post_json(
        search_url,
        request_body,
        max_bytes=cfg.max_characteristics_bytes,
    )
    if status != 200:
        raise ValueError(f"Unexpected BHR-G characteristics HTTP status: {status}")
    if not _allowed_final_url(final_url, search_url):
        raise ValueError(f"Unexpected BHR-G characteristics final URL: {final_url}")
    if len(payload) > cfg.max_characteristics_bytes:
        raise ValueError("BHR-G characteristics response exceeds configured byte guardrail")

    characteristics_path = out / "bhrg_characteristics_response.xml"
    characteristics_path.write_bytes(payload)
    bro_ids = parse_characteristics_response(payload, max_results=cfg.max_results)

    objects: list[dict] = []
    total_object_bytes = 0
    for bro_id in bro_ids:
        object_url = build_object_url(bro_id, base_url=cfg.base_url)
        object_payload, object_headers, object_final_url, object_status = client.get(
            object_url,
            max_bytes=cfg.max_object_bytes,
        )
        if object_status != 200:
            raise ValueError(f"Unexpected BHR-G object HTTP status for {bro_id}: {object_status}")
        if not _allowed_final_url(object_final_url, object_url):
            raise ValueError(f"Unexpected BHR-G object final URL for {bro_id}: {object_final_url}")
        if len(object_payload) > cfg.max_object_bytes:
            raise ValueError(f"BHR-G object response exceeds guardrail for {bro_id}")

        object_ids = _extract_bhr_ids(object_payload)
        if bro_id not in object_ids:
            raise ValueError(
                f"BHR-G object BRO-ID mismatch for {bro_id}: response ids={sorted(object_ids)}"
            )
        object_file = f"bhrg_object_{bro_id}.xml"
        (out / object_file).write_bytes(object_payload)
        total_object_bytes += len(object_payload)
        objects.append(
            {
                "bro_id": bro_id,
                "requested_url": object_url,
                "final_url": object_final_url,
                "artifact_file": object_file,
                "bytes": len(object_payload),
                "sha256": hashlib.sha256(object_payload).hexdigest(),
                "content_type": object_headers.get("content-type"),
            }
        )

    lon, lat = rd_to_wgs84(cfg.x_rd, cfg.y_rd)
    manifest = {
        "capability": "STAGE_B_LOCAL_BHRG_20774_ACQUISITION",
        "target": {
            "gmw": cfg.target_gmw,
            "station": cfg.target_station,
            "rd_x_m": cfg.x_rd,
            "rd_y_m": cfg.y_rd,
            "wgs84_lon": lon,
            "wgs84_lat": lat,
        },
        "search": {
            "radius_km": cfg.radius_km,
            "radius_role": "acquisition_window_only_not_scientific_threshold",
            "requested_url": search_url,
            "final_url": final_url,
            "request_file": request_path.name,
            "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
            "response_file": characteristics_path.name,
            "response_sha256": hashlib.sha256(payload).hexdigest(),
            "response_bytes": len(payload),
            "content_type": headers.get("content-type"),
            "declared_result_limit": cfg.max_results,
        },
        "result": {
            "state": "NO_LOCAL_BHRG_FOUND" if not bro_ids else "LOCAL_BHRG_OBJECTS_ACQUIRED",
            "count": len(bro_ids),
            "bro_ids": bro_ids,
            "objects": objects,
            "total_object_bytes": total_object_bytes,
        },
        "guardrails": {
            "source": "BRO_BHR_G_PUBLIC_REST",
            "raw_only": True,
            "lithology_interpretation_performed": False,
            "hydraulic_interpretation_performed": False,
            "screen_correlation_performed": False,
            "interpolation_performed": False,
            "geotop_used": False,
            "admission_decision_performed": False,
            "allow_admissible_enabled": False,
        },
        "qualification_boundary": (
            "Local BHR-G discovery and raw object acquisition for GMW000000020774 only. "
            "No material/lithological interpretation, screen correlation, hydraulic continuity "
            "inference or Stage-B admission."
        ),
    }
    (out / "bhrg_local_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest
