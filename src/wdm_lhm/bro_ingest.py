from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import csv
import hashlib
import io
import json
import re
import time

import numpy as np
import pandas as pd
from pyproj import Transformer


PDOK_GM_BASE = "https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/ogc/v1"
BRO_GLD_BASE = "https://publiek.broservices.nl/gm/gld/v1"
WDM_WMS = "https://service.pdok.nl/tno/bro-model-grondwaterspiegeldiepte/wms/v2_0"


@dataclass(frozen=True)
class BROIngestConfig:
    bbox_crs84: tuple[float, float, float, float]
    min_observations: int = 30
    min_span_days: int = 365
    prefer_fully_assessed: bool = True
    allow_preliminary: bool = True
    include_unknown_series: bool = False
    require_ground_level: bool = True
    only_tubes_in_use: bool = False
    max_series: int | None = None
    page_limit: int = 1000
    request_timeout_s: int = 60
    gld_requests_per_second: float = 2.5
    user_agent: str = "wdm-lhm-ts06/0.6 (+research; public BRO/PDOK services)"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["bbox_crs84"] = list(self.bbox_crs84)
        return d


class HttpCacheClient:
    """Small deterministic HTTP client with immutable URL-keyed cache.

    A transport can be injected for tests. The default uses urllib and therefore
    requires normal internet access on the machine where TS06 is run.
    """

    def __init__(self, cache_dir: str | Path, timeout_s: int = 60,
                 user_agent: str = BROIngestConfig((0, 0, 0, 0)).user_agent,
                 transport: Callable[[str, dict[str, str], int], bytes] | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_s = timeout_s
        self.user_agent = user_agent
        self.transport = transport or self._urllib_transport

    @staticmethod
    def _urllib_transport(url: str, headers: dict[str, str], timeout_s: int) -> bytes:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout_s) as r:
            return r.read()

    def _paths(self, url: str) -> tuple[Path, Path]:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.bin", self.cache_dir / f"{h}.json"

    def get_bytes(self, url: str, accept: str = "*/*", force: bool = False) -> bytes:
        data_path, meta_path = self._paths(url)
        if data_path.exists() and not force:
            return data_path.read_bytes()
        headers = {"User-Agent": self.user_agent, "Accept": accept}
        payload = self.transport(url, headers, self.timeout_s)
        data_path.write_bytes(payload)
        meta_path.write_text(json.dumps({
            "url": url,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "retrieved_unix": time.time(),
            "accept": accept,
        }, indent=2), encoding="utf-8")
        return payload

    def get_json(self, url: str, force: bool = False) -> dict:
        return json.loads(self.get_bytes(url, "application/geo+json,application/json", force).decode("utf-8"))


def _build_url(base: str, params: dict[str, Any]) -> str:
    return f"{base}?{urlencode(params, doseq=True)}"


def fetch_collection(client: HttpCacheClient, collection: str, bbox: tuple[float, float, float, float],
                     page_limit: int = 1000, max_pages: int = 100) -> dict:
    """Fetch an OGC API Features collection within a CRS84 bbox, following rel=next."""
    base = f"{PDOK_GM_BASE}/collections/{collection}/items"
    url = _build_url(base, {"bbox": ",".join(map(str, bbox)), "limit": page_limit, "f": "json"})
    features: list[dict] = []
    pages = 0
    seen: set[str] = set()
    while url:
        if url in seen:
            raise RuntimeError("OGC pagination loop detected")
        seen.add(url)
        obj = client.get_json(url)
        features.extend(obj.get("features", []))
        pages += 1
        if pages >= max_pages:
            raise RuntimeError(f"OGC pagination exceeded max_pages={max_pages}")
        next_urls = [x.get("href") for x in obj.get("links", []) if x.get("rel") == "next" and x.get("href")]
        url = next_urls[0] if next_urls else None
    return {"type": "FeatureCollection", "features": features, "numberReturned": len(features), "pages": pages}


def features_to_frame(fc: dict) -> pd.DataFrame:
    rows: list[dict] = []
    for f in fc.get("features", []):
        row = dict(f.get("properties") or {})
        row["feature_id"] = f.get("id")
        geom = f.get("geometry") or {}
        coords = geom.get("coordinates")
        if geom.get("type") == "Point" and coords and len(coords) >= 2:
            row["lon"] = float(coords[0]); row["lat"] = float(coords[1])
        rows.append(row)
    return pd.DataFrame(rows)


def _normalize_col(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def _clean_assessment_status(value):
    if value is None or pd.isna(value):
        return pd.NA
    text = str(value).strip()
    return text if text else pd.NA


def _normalize_assessment_status(value):
    raw = _clean_assessment_status(value)
    if pd.isna(raw):
        return pd.NA
    return str(raw).casefold()


def _read_csv_flexible(payload: bytes) -> pd.DataFrame:
    text = payload.decode("utf-8-sig", errors="replace")
    try:
        df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    except Exception:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        df = pd.read_csv(io.StringIO(text), sep=dialect.delimiter)
    return df.dropna(axis=1, how="all")


def _read_headerless_compact_csv(payload: bytes) -> pd.DataFrame | None:
    """Recognize the current BRO compact GLD positional format conservatively."""
    text = payload.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
        sep = dialect.delimiter
    except Exception:
        sep = ","
    try:
        raw = pd.read_csv(io.StringIO(text), sep=sep, header=None, engine="python")
    except Exception:
        return None
    raw = raw.dropna(axis=1, how="all").dropna(axis=0, how="all")
    if raw.shape[1] < 2 or raw.empty:
        return None
    times = pd.to_datetime(raw.iloc[:, 0], errors="coerce", utc=True)
    values = pd.to_numeric(raw.iloc[:, 1].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    valid = times.notna() & values.notna()
    if valid.sum() < 2 or valid.mean() < 0.95:
        return None
    out = raw.loc[valid].copy()
    out.columns = [f"field_{i}" for i in range(out.shape[1])]
    out["__parsed_time"] = times.loc[valid].to_numpy()
    out["__parsed_value"] = values.loc[valid].to_numpy()
    return out


def parse_gld_compact_csv(payload: bytes, *, gld_bro_id: str, station_id: str,
                          series_class: str) -> pd.DataFrame:
    """Parse BRO compact GLD CSV while preserving row-level assessment provenance."""
    output_columns = [
        "date", "station_id", "obs_head_mnap", "gld_bro_id", "series_class",
        "assessment_status_raw", "assessment_status", "source",
    ]
    df = _read_csv_flexible(payload)
    if df.empty:
        return pd.DataFrame(columns=output_columns)

    norm = {_normalize_col(c): c for c in df.columns}
    time_candidates = [
        "tijdstipmeting", "tijdstip", "meetdatumtijd", "datumtijd", "measurementtime",
        "phenomenontime", "time", "datetime", "datum",
    ]
    value_candidates = [
        "waterstand", "napstand", "grondwaterstand", "meetwaarde", "measurementvalue",
        "value", "waarde",
    ]
    assessment_candidates = [
        "statuskwaliteitscontrole", "kwaliteitscontrolestatus", "statusbeoordeling",
        "beoordelingsstatus", "assessmentstatus", "qualitycontrolstatus",
    ]
    tcol = next((norm[c] for c in time_candidates if c in norm), None)
    vcol = next((norm[c] for c in value_candidates if c in norm), None)
    acol = next((norm[c] for c in assessment_candidates if c in norm), None)
    if tcol is not None and vcol is not None:
        status_raw = df[acol] if acol is not None else pd.Series(pd.NA, index=df.index, dtype="object")
        out = pd.DataFrame({
            "date": pd.to_datetime(df[tcol], errors="coerce", utc=True),
            "obs_head_mnap": pd.to_numeric(df[vcol].astype(str).str.replace(",", ".", regex=False), errors="coerce"),
            "assessment_status_raw": status_raw,
        }).dropna(subset=["date", "obs_head_mnap"])
    else:
        positional = _read_headerless_compact_csv(payload)
        if positional is None:
            raise ValueError(
                "BRO GLD compact CSV schema not recognized; refusing heuristic value selection. "
                f"columns={list(df.columns)}"
            )
        status_raw = (
            positional["field_2"]
            if "field_2" in positional.columns
            else pd.Series(pd.NA, index=positional.index, dtype="object")
        )
        out = pd.DataFrame({
            "date": positional["__parsed_time"],
            "obs_head_mnap": positional["__parsed_value"],
            "assessment_status_raw": status_raw,
        }).dropna(subset=["date", "obs_head_mnap"])

    out["assessment_status_raw"] = out["assessment_status_raw"].map(_clean_assessment_status)
    out["assessment_status"] = out["assessment_status_raw"].map(_normalize_assessment_status)
    out["date"] = out["date"].dt.tz_convert("Europe/Amsterdam").dt.tz_localize(None)
    out["station_id"] = station_id
    out["gld_bro_id"] = gld_bro_id
    out["series_class"] = series_class
    out["source"] = "BRO_GLD"
    return out[output_columns].sort_values("date").drop_duplicates(["station_id", "date"], keep="last")


def _pick_series_url(row: pd.Series, cfg: BROIngestConfig) -> tuple[str | None, str | None]:
    choices: list[tuple[str, str]] = []
    if cfg.prefer_fully_assessed:
        choices.append(("series_fully_assessed_csv_url", "fully_assessed"))
    if cfg.allow_preliminary:
        choices.append(("series_preliminary_csv_url", "preliminary"))
    if cfg.include_unknown_series:
        choices.append(("series_unknown_csv_url", "unknown"))
    if not cfg.prefer_fully_assessed:
        choices.append(("series_fully_assessed_csv_url", "fully_assessed"))
    for col, label in choices:
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            return str(val).strip(), label
    return None, None


def _join_metadata(gmw: pd.DataFrame, tubes: pd.DataFrame, gld: pd.DataFrame, cfg: BROIngestConfig) -> pd.DataFrame:
    for col in ["gm_gmw_pk", "ground_level_position", "bro_id"]:
        if col not in gmw.columns:
            gmw[col] = np.nan
    for col in ["gm_gmw_fk", "gm_gmw_monitoringtube_pk", "gmw_bro_id", "tube_number"]:
        if col not in tubes.columns:
            tubes[col] = np.nan
    for col in ["gm_gmw_monitoringtube_fk", "bro_id", "number_of_observations", "research_first_date", "research_last_date"]:
        if col not in gld.columns:
            gld[col] = np.nan

    gmw_small = gmw[[c for c in ["gm_gmw_pk", "bro_id", "ground_level_position", "lon", "lat", "quality_regime", "nitg_code", "well_code"] if c in gmw.columns]].copy()
    gmw_small = gmw_small.rename(columns={"bro_id": "gmw_bro_id_parent", "quality_regime": "gmw_quality_regime"})
    joined_tube = tubes.merge(gmw_small, left_on="gm_gmw_fk", right_on="gm_gmw_pk", how="left", suffixes=("", "_gmw"))

    gld2 = gld.rename(columns={"bro_id": "gld_bro_id", "quality_regime": "gld_quality_regime"})
    joined = gld2.merge(joined_tube, left_on="gm_gmw_monitoringtube_fk", right_on="gm_gmw_monitoringtube_pk", how="inner", suffixes=("", "_tube"))

    if cfg.only_tubes_in_use and "tube_in_use" in joined.columns:
        joined = joined[joined["tube_in_use"].astype(str).str.lower().isin({"ja", "yes", "true"})]
    joined["number_of_observations"] = pd.to_numeric(joined["number_of_observations"], errors="coerce").fillna(0).astype(int)
    joined["research_first_date"] = pd.to_datetime(joined["research_first_date"], errors="coerce")
    joined["research_last_date"] = pd.to_datetime(joined["research_last_date"], errors="coerce")
    joined["span_days"] = (joined["research_last_date"] - joined["research_first_date"]).dt.days + 1
    joined = joined[(joined["number_of_observations"] >= cfg.min_observations) & (joined["span_days"] >= cfg.min_span_days)]
    if cfg.require_ground_level:
        joined = joined[pd.to_numeric(joined["ground_level_position"], errors="coerce").notna()]
    joined["station_id"] = joined["gmw_bro_id"].astype(str) + "_T" + joined["tube_number"].astype("Int64").astype(str)
    return joined.sort_values(["station_id", "research_first_date", "gld_bro_id"])


def _make_station_table(meta: pd.DataFrame) -> pd.DataFrame:
    if meta.empty:
        return pd.DataFrame(columns=["station_id", "x_rd", "y_rd", "ground_level_mnap", "used_in_wdm", "used_in_lhm_calibration", "heldout_group", "metadata_source"])
    lon = meta["lon"] if "lon" in meta.columns else meta.get("lon_gmw")
    lat = meta["lat"] if "lat" in meta.columns else meta.get("lat_gmw")
    if lon is None or lat is None:
        raise ValueError("BRO metadata lacks standardized location coordinates")
    tr = Transformer.from_crs("EPSG:4326", "EPSG:28992", always_xy=True)
    lon_arr = pd.to_numeric(lon, errors="coerce").to_numpy(dtype=float)
    lat_arr = pd.to_numeric(lat, errors="coerce").to_numpy(dtype=float)
    x, y = tr.transform(lon_arr.tolist(), lat_arr.tolist())
    out = pd.DataFrame({
        "station_id": meta["station_id"].astype(str),
        "x_rd": x,
        "y_rd": y,
        "ground_level_mnap": pd.to_numeric(meta["ground_level_position"], errors="coerce"),
        "used_in_wdm": "unknown",
        "used_in_lhm_calibration": "unknown",
        "heldout_group": "unknown",
        "metadata_source": "BRO_GMW_GLD",
        "gmw_bro_id": meta["gmw_bro_id"].astype(str),
        "tube_number": meta["tube_number"],
        "gld_bro_id": meta["gld_bro_id"].astype(str),
        "screen_top_position_mnap": pd.to_numeric(meta.get("screen_top_position"), errors="coerce"),
        "screen_bottom_position_mnap": pd.to_numeric(meta.get("screen_bottom_position"), errors="coerce"),
        "tube_status": meta.get("tube_status"),
        "tube_in_use": meta.get("tube_in_use"),
    })
    return out.sort_values(["station_id", "gld_bro_id"]).drop_duplicates("station_id", keep="first")


def ingest_bro_groundwater(output_dir: str | Path, config: BROIngestConfig,
                           *, transport: Callable[[str, dict[str, str], int], bytes] | None = None,
                           force: bool = False) -> dict:
    out = Path(output_dir)
    raw = out / "raw_cache"
    bundle = out / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    client = HttpCacheClient(raw, config.request_timeout_s, config.user_agent, transport)

    collections: dict[str, pd.DataFrame] = {}
    for name in ("gm_gmw", "gm_gmw_monitoringtube", "gm_gld"):
        fc = fetch_collection(client, name, config.bbox_crs84, config.page_limit)
        (bundle / f"{name}.geojson").write_text(json.dumps(fc), encoding="utf-8")
        collections[name] = features_to_frame(fc)
        collections[name].to_csv(bundle / f"{name}.csv", index=False)

    meta = _join_metadata(collections["gm_gmw"], collections["gm_gmw_monitoringtube"], collections["gm_gld"], config)
    if config.max_series is not None:
        meta = meta.head(config.max_series)
    meta.to_csv(bundle / "bro_series_catalog.csv", index=False)
    stations = _make_station_table(meta)
    stations.to_csv(bundle / "stations.csv", index=False)

    observations: list[pd.DataFrame] = []
    failures: list[dict] = []
    last_gld_request = 0.0
    min_interval = 1.0 / max(config.gld_requests_per_second, 0.01)
    for row in meta.itertuples(index=False):
        s = pd.Series(row._asdict())
        url, series_class = _pick_series_url(s, config)
        if not url:
            failures.append({"gld_bro_id": s.get("gld_bro_id"), "station_id": s.get("station_id"), "stage": "select_series", "error": "no permitted series URL"})
            continue
        sleep_for = min_interval - (time.monotonic() - last_gld_request)
        if sleep_for > 0 and transport is None:
            time.sleep(sleep_for)
        try:
            payload = client.get_bytes(url, "text/csv,*/*;q=0.5", force=force)
            last_gld_request = time.monotonic()
            parsed = parse_gld_compact_csv(payload, gld_bro_id=str(s["gld_bro_id"]), station_id=str(s["station_id"]), series_class=str(series_class))
            if parsed.empty and series_class == "fully_assessed" and config.allow_preliminary:
                alt = s.get("series_preliminary_csv_url")
                if pd.notna(alt) and str(alt).strip() and str(alt).strip() != url:
                    payload = client.get_bytes(str(alt).strip(), "text/csv,*/*;q=0.5", force=force)
                    parsed = parse_gld_compact_csv(payload, gld_bro_id=str(s["gld_bro_id"]), station_id=str(s["station_id"]), series_class="preliminary")
            observations.append(parsed)
        except Exception as exc:
            failures.append({"gld_bro_id": s.get("gld_bro_id"), "station_id": s.get("station_id"), "stage": "download_or_parse_series", "error": f"{type(exc).__name__}: {exc}"})

    obs = pd.concat(observations, ignore_index=True) if observations else pd.DataFrame(columns=[
        "date", "station_id", "obs_head_mnap", "gld_bro_id", "series_class",
        "assessment_status_raw", "assessment_status", "source",
    ])
    obs.to_csv(bundle / "observations.csv", index=False)
    pd.DataFrame(failures).to_csv(bundle / "ingest_failures.csv", index=False)

    assessment_status_counts: dict[str, int] = {}
    if "assessment_status" in obs.columns:
        statuses = obs["assessment_status"].astype("string").fillna("<missing>")
        assessment_status_counts = {str(k): int(v) for k, v in statuses.value_counts().items()}

    manifest = {
        "capability": "TS06_BRO_INGEST",
        "config": config.as_dict(),
        "services": {"pdok_gm_base": PDOK_GM_BASE, "bro_gld_base": BRO_GLD_BASE, "wdm_wms": WDM_WMS},
        "counts": {
            "gmw": int(len(collections["gm_gmw"])),
            "monitoring_tubes": int(len(collections["gm_gmw_monitoringtube"])),
            "gld_objects": int(len(collections["gm_gld"])),
            "selected_series": int(len(meta)),
            "stations": int(stations["station_id"].nunique()) if not stations.empty else 0,
            "observations": int(len(obs)),
            "failures": int(len(failures)),
        },
        "assessment_status_counts": assessment_status_counts,
        "assessment_status_policy": "row-level BRO assessment is preserved at ingest; scientific eligibility is decided downstream and missing status is never assumed approved",
        "lineage_policy": "used_in_wdm and used_in_lhm_calibration remain unknown until audited; heldout_group remains unknown until study design",
        "qualification_boundary": "BRO/PDOK ingest only; no assertion that selected tubes represent the phreatic water table and no LHM comparison yet",
    }
    (bundle / "ingest_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"manifest": manifest, "stations": stations, "observations": obs, "catalog": meta, "failures": pd.DataFrame(failures), "bundle_dir": bundle}