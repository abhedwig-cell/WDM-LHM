from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations

import numpy as np
import pandas as pd


PRESCREEN_VERDICTS = {
    "CANDIDATE_FREATIC",
    "REVIEW_DEEP_OR_AMBIGUOUS",
    "INSUFFICIENT_DATA",
    "NOT_USABLE_SERIES",
}
ADMISSION_VERDICTS = {
    "ADMISSIBLE_FREATIC",
    "REVIEW_REQUIRED",
    "NOT_ADMISSIBLE_FREATIC",
    "INSUFFICIENT_DATA",
}
APPROVED_ASSESSMENT_STATUS = "goedgekeurd"
REJECTED_ASSESSMENT_STATUS = "afgekeurd"
UNDECIDED_ASSESSMENT_STATUS = "onbeslist"


@dataclass(frozen=True)
class FreaticScreeningConfig:
    """Policy parameters for the BRO-only pre-screen.

    The legacy 5 m threshold is retained as an explicitly labelled historical
    groundwater-dynamics routing criterion. It is not treated as a physical
    definition of freatic connection.
    """

    min_observations: int = 100
    min_span_days: int = 730
    legacy_max_screen_bottom_depth_m: float = 5.0
    require_fully_assessed_for_candidate: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


def _reason_join(reasons: list[str]) -> str:
    return "|".join(sorted(dict.fromkeys(reasons)))


def _safe_text(value) -> str | None:
    if value is None or pd.isna(value):
        return None
    s = str(value).strip()
    return s if s else None


def _series_class(obs: pd.DataFrame, station_row: pd.Series) -> str | None:
    direct = _safe_text(station_row.get("series_class"))
    if direct:
        return direct.lower()
    if "series_class" in obs.columns:
        values = [str(v).strip().lower() for v in obs["series_class"].dropna().unique() if str(v).strip()]
        if len(values) == 1:
            return values[0]
        if len(values) > 1:
            return "mixed:" + ",".join(sorted(values))
    return None


def _normalized_assessment_status(obs: pd.DataFrame) -> pd.Series:
    if "assessment_status" not in obs.columns:
        return pd.Series(pd.NA, index=obs.index, dtype="string")
    values = obs["assessment_status"].astype("string").str.strip().str.casefold()
    return values.mask(values == "", pd.NA)


def _select_scientific_observations(obs: pd.DataFrame, series_class: str | None) -> tuple[pd.DataFrame, dict[str, int | bool]]:
    """Select rows eligible for scientific evidence without deleting provenance.

    For a fully assessed BRO series only rows explicitly marked `goedgekeurd`
    are eligible. Rejected, undecided and unknown rows remain present in the
    input bundle but are not positive scientific evidence. Other series classes
    retain their existing behaviour in this bounded workunit.
    """

    statuses = _normalized_assessment_status(obs)
    status_available = "assessment_status" in obs.columns
    approved = statuses.eq(APPROVED_ASSESSMENT_STATUS).fillna(False)
    rejected = statuses.eq(REJECTED_ASSESSMENT_STATUS).fillna(False)
    undecided = statuses.eq(UNDECIDED_ASSESSMENT_STATUS).fillna(False)
    unknown = statuses.isna()
    recognized = approved | rejected | undecided | unknown
    other = ~recognized

    stats: dict[str, int | bool] = {
        "raw_count": int(len(obs)),
        "approved_count": int(approved.sum()),
        "rejected_count": int(rejected.sum()),
        "undecided_count": int(undecided.sum()),
        "unknown_count": int(unknown.sum()),
        "other_count": int(other.sum()),
        "status_available": bool(status_available),
    }

    if series_class == "fully_assessed":
        selected = obs.loc[approved].copy()
    else:
        selected = obs.copy()
    stats["eligible_count"] = int(len(selected))
    return selected, stats


def freatic_prescreen(
    stations: pd.DataFrame,
    observations: pd.DataFrame,
    config: FreaticScreeningConfig | None = None,
) -> pd.DataFrame:
    """Build a conservative BRO-only candidate screen for freatic use.

    `CANDIDATE_FREATIC` is a routing result, not final scientific admission.
    The final admission requires additional evidence through `freatic_admission`.
    """

    cfg = config or FreaticScreeningConfig()
    required_station = {"station_id", "ground_level_mnap", "screen_top_position_mnap", "screen_bottom_position_mnap"}
    required_obs = {"station_id", "date", "obs_head_mnap"}
    missing_s = sorted(required_station - set(stations.columns))
    missing_o = sorted(required_obs - set(observations.columns))
    if missing_s or missing_o:
        raise ValueError(f"missing required columns stations={missing_s}; observations={missing_o}")

    obs = observations.copy()
    obs["date"] = pd.to_datetime(obs["date"], errors="coerce")
    obs["obs_head_mnap"] = pd.to_numeric(obs["obs_head_mnap"], errors="coerce")

    rows: list[dict] = []
    for _, st in stations.iterrows():
        sid = str(st["station_id"])
        so_raw = obs[obs["station_id"].astype(str) == sid].dropna(subset=["date", "obs_head_mnap"]).copy()
        reasons: list[str] = []

        series_class = _series_class(so_raw, st)
        so, quality = _select_scientific_observations(so_raw, series_class)
        if series_class == "fully_assessed":
            if not bool(quality["status_available"]):
                reasons.append("ROW_ASSESSMENT_STATUS_UNAVAILABLE")
            excluded = int(quality["raw_count"]) - int(quality["eligible_count"])
            if excluded > 0:
                reasons.append("NON_APPROVED_ROWS_EXCLUDED")
            if int(quality["other_count"]) > 0:
                reasons.append("UNRECOGNIZED_ASSESSMENT_STATUS_EXCLUDED")

        ground = pd.to_numeric(pd.Series([st.get("ground_level_mnap")]), errors="coerce").iloc[0]
        ztop = pd.to_numeric(pd.Series([st.get("screen_top_position_mnap")]), errors="coerce").iloc[0]
        zbot = pd.to_numeric(pd.Series([st.get("screen_bottom_position_mnap")]), errors="coerce").iloc[0]

        geometry_ok = bool(np.isfinite(ground) and np.isfinite(ztop) and np.isfinite(zbot))
        screen_top_depth = np.nan
        screen_bottom_depth = np.nan
        if geometry_ok:
            screen_top_depth = float(ground - ztop)
            screen_bottom_depth = float(ground - zbot)
            if ztop < zbot or screen_top_depth < 0 or screen_bottom_depth < screen_top_depth:
                geometry_ok = False
                reasons.append("INVALID_SCREEN_GEOMETRY")
        else:
            reasons.append("MISSING_SCREEN_OR_GROUND_LEVEL")

        n = int(len(so))
        span_days = 0
        if n:
            span_days = int((so["date"].max() - so["date"].min()).days + 1)
        series_ok = n >= cfg.min_observations and span_days >= cfg.min_span_days
        if n < cfg.min_observations:
            reasons.append("TOO_FEW_OBSERVATIONS")
        if span_days < cfg.min_span_days:
            reasons.append("RECORD_TOO_SHORT")

        q05 = q50 = q95 = above_ground_fraction = np.nan
        if n and np.isfinite(ground):
            depths = ground - so["obs_head_mnap"].astype(float)
            q05, q50, q95 = [float(depths.quantile(p)) for p in (0.05, 0.50, 0.95)]
            above_ground_fraction = float((depths < 0).mean())

        fully_assessed = series_class == "fully_assessed"
        if cfg.require_fully_assessed_for_candidate and not fully_assessed:
            reasons.append("SERIES_NOT_UNIQUELY_FULLY_ASSESSED")

        legacy_depth_risk = False
        envelope_gap = np.nan
        if geometry_ok:
            legacy_depth_risk = bool(screen_bottom_depth > cfg.legacy_max_screen_bottom_depth_m)
            if legacy_depth_risk:
                reasons.append("LEGACY_GD_DEPTH_RISK")
            if np.isfinite(q95):
                envelope_gap = float(screen_top_depth - q95)

        tube_status = _safe_text(st.get("tube_status"))
        tube_in_use = _safe_text(st.get("tube_in_use"))
        if tube_status is None:
            reasons.append("TUBE_STATUS_UNKNOWN")
        if tube_in_use is None or tube_in_use.lower() in {"onbekend", "unknown"}:
            reasons.append("TUBE_IN_USE_UNKNOWN")

        if not geometry_ok:
            verdict = "INSUFFICIENT_DATA"
        elif not series_ok:
            verdict = "NOT_USABLE_SERIES"
        elif legacy_depth_risk or (cfg.require_fully_assessed_for_candidate and not fully_assessed):
            verdict = "REVIEW_DEEP_OR_AMBIGUOUS"
        else:
            verdict = "CANDIDATE_FREATIC"

        rows.append({
            "station_id": sid,
            "gmw_bro_id": st.get("gmw_bro_id"),
            "tube_number": st.get("tube_number"),
            "gld_bro_id": st.get("gld_bro_id"),
            "screen_top_depth_m": screen_top_depth,
            "screen_bottom_depth_m": screen_bottom_depth,
            "n_observations_raw": int(quality["raw_count"]),
            "n_observations": n,
            "n_assessment_approved": int(quality["approved_count"]),
            "n_assessment_rejected": int(quality["rejected_count"]),
            "n_assessment_undecided": int(quality["undecided_count"]),
            "n_assessment_unknown": int(quality["unknown_count"]),
            "n_assessment_other": int(quality["other_count"]),
            "record_span_days": span_days,
            "q05_depth_m": q05,
            "q50_depth_m": q50,
            "q95_depth_m": q95,
            "above_ground_fraction": above_ground_fraction,
            "legacy_gd_depth_risk": legacy_depth_risk,
            "screen_below_empirical_envelope_m": envelope_gap,
            "tube_status": tube_status,
            "tube_in_use": tube_in_use,
            "series_class": series_class,
            "prescreen_verdict": verdict,
            "reason_codes": _reason_join(reasons),
        })

    return pd.DataFrame(rows).sort_values("station_id").reset_index(drop=True)


def vertical_head_pair_evidence(
    stations: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    min_overlap_days: int = 30,
) -> pd.DataFrame:
    """Summarize daily contemporaneous head differences between same-GMW filters.

    No universal significance threshold is applied. The output is evidence for
    later hydrogeological interpretation, not an automatic rejection decision.
    Row-level BRO assessment status is applied before daily aggregation.
    """

    req_s = {"station_id", "gmw_bro_id", "ground_level_mnap", "screen_top_position_mnap", "screen_bottom_position_mnap"}
    req_o = {"station_id", "date", "obs_head_mnap"}
    if req_s - set(stations.columns) or req_o - set(observations.columns):
        raise ValueError("required station/observation columns missing for vertical-head evidence")

    obs = observations.copy()
    obs["date"] = pd.to_datetime(obs["date"], errors="coerce")
    obs["obs_head_mnap"] = pd.to_numeric(obs["obs_head_mnap"], errors="coerce")

    eligible_parts: list[pd.DataFrame] = []
    for _, station_group in obs.dropna(subset=["date", "obs_head_mnap"]).groupby("station_id", sort=False):
        series_class = _series_class(station_group, pd.Series(dtype="object"))
        selected, _ = _select_scientific_observations(station_group, series_class)
        if not selected.empty:
            eligible_parts.append(selected)
    if eligible_parts:
        obs = pd.concat(eligible_parts, ignore_index=True)
    else:
        obs = obs.iloc[0:0].copy()

    obs["day"] = obs["date"].dt.floor("D")
    daily = obs.dropna(subset=["day", "obs_head_mnap"]).groupby(["station_id", "day"], as_index=False)["obs_head_mnap"].median()

    out: list[dict] = []
    for gmw, group in stations.dropna(subset=["gmw_bro_id"]).groupby("gmw_bro_id"):
        if len(group) < 2:
            continue
        for (_, a), (_, b) in combinations(group.iterrows(), 2):
            def midpoint_depth(r: pd.Series) -> float:
                ground = float(r["ground_level_mnap"])
                top = float(r["screen_top_position_mnap"])
                bot = float(r["screen_bottom_position_mnap"])
                return ground - 0.5 * (top + bot)

            try:
                da, db = midpoint_depth(a), midpoint_depth(b)
            except Exception:
                continue
            shallow, deep = (a, b) if da <= db else (b, a)
            shallow_depth, deep_depth = (da, db) if da <= db else (db, da)

            sa = daily[daily["station_id"].astype(str) == str(shallow["station_id"])][["day", "obs_head_mnap"]].rename(columns={"obs_head_mnap": "h_shallow"})
            sb = daily[daily["station_id"].astype(str) == str(deep["station_id"])][["day", "obs_head_mnap"]].rename(columns={"obs_head_mnap": "h_deep"})
            pair = sa.merge(sb, on="day", how="inner")
            n = int(len(pair))
            if n:
                delta = pair["h_shallow"] - pair["h_deep"]
                med = float(delta.median())
                mad_sigma = float(1.4826 * (delta - med).abs().median())
                pos_frac = float((delta > 0).mean())
                neg_frac = float((delta < 0).mean())
                corr = float(pair[["h_shallow", "h_deep"]].corr().iloc[0, 1]) if n >= 2 else np.nan
                span = int((pair["day"].max() - pair["day"].min()).days + 1)
            else:
                med = mad_sigma = pos_frac = neg_frac = corr = np.nan
                span = 0
            status = "EVIDENCE_AVAILABLE" if n >= min_overlap_days else "INSUFFICIENT_OVERLAP"
            out.append({
                "gmw_bro_id": gmw,
                "shallow_station_id": str(shallow["station_id"]),
                "deep_station_id": str(deep["station_id"]),
                "shallow_screen_mid_depth_m": shallow_depth,
                "deep_screen_mid_depth_m": deep_depth,
                "overlap_days": n,
                "overlap_span_days": span,
                "median_shallow_minus_deep_head_m": med,
                "robust_sigma_head_difference_m": mad_sigma,
                "positive_sign_fraction": pos_frac,
                "negative_sign_fraction": neg_frac,
                "daily_head_correlation": corr,
                "vertical_head_evidence_status": status,
            })

    return pd.DataFrame(out)


def freatic_admission(
    prescreen: pd.DataFrame,
    evidence: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Apply conservative Stage-B admission semantics with explicit evidence."""

    required = {"station_id", "prescreen_verdict"}
    missing = required - set(prescreen.columns)
    if missing:
        raise ValueError(f"missing prescreen columns: {sorted(missing)}")

    result = prescreen.copy()
    if evidence is None:
        ev = pd.DataFrame({"station_id": result["station_id"]})
    else:
        if "station_id" not in evidence.columns:
            raise ValueError("evidence must contain station_id")
        ev = evidence.copy()
    for col in ("hydrogeology_evidence", "vertical_head_assessment", "design_evidence"):
        if col not in ev.columns:
            ev[col] = "unknown"
    result = result.merge(ev[["station_id", "hydrogeology_evidence", "vertical_head_assessment", "design_evidence"]], on="station_id", how="left")
    for col in ("hydrogeology_evidence", "vertical_head_assessment", "design_evidence"):
        result[col] = result[col].fillna("unknown").astype(str).str.lower()

    verdicts: list[str] = []
    reasons_out: list[str] = []
    for _, row in result.iterrows():
        reasons: list[str] = []
        pre = row["prescreen_verdict"]
        hydro = row["hydrogeology_evidence"]
        vert = row["vertical_head_assessment"]
        design = row["design_evidence"]

        if pre in {"INSUFFICIENT_DATA", "NOT_USABLE_SERIES"}:
            verdict = "INSUFFICIENT_DATA"
            reasons.append("PRESCREEN_NOT_SCIENTIFICALLY_USABLE")
        elif hydro == "confined_or_separated" or vert == "incompatible" or design == "non_freatic_design":
            verdict = "NOT_ADMISSIBLE_FREATIC"
            reasons.append("POSITIVE_NON_FREATIC_EVIDENCE")
        elif (hydro == "freatic_unconfined" or design == "freatic_design") and vert != "incompatible":
            verdict = "ADMISSIBLE_FREATIC"
            reasons.append("POSITIVE_FREATIC_EVIDENCE")
        else:
            verdict = "REVIEW_REQUIRED"
            reasons.append("FREATIC_CONNECTION_NOT_PROVEN")

        verdicts.append(verdict)
        reasons_out.append(_reason_join(reasons))

    result["admission_verdict"] = verdicts
    result["admission_reason_codes"] = reasons_out
    return result
