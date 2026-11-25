"""
Offline Application Funnel & Conversion Reporter (`forge report`).
Computes stage conversion metrics, CV version performance, and response rates
directly from the local SQLite database. Zero network requests.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from careerforge.core.store import CareerStore, parse_iso
except ImportError:
    from core.store import CareerStore, parse_iso

FUNNEL_ORDER = ("saved", "applied", "screen", "interview", "offer")
RESPONSE_STAGES = ("screen", "interview", "offer")
SPARK_BLOCKS = "▁▂▃▄▅▆▇█"


class ReportError(Exception):
    """Raised on invalid report parameters such as malformed --since dates."""


def parse_since(since_str: Optional[str], now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parses a `--since` filter string.
    Accepts relative windows like '30d', '90d' or ISO dates like '2026-11-01'.
    """
    if not since_str:
        return None

    clean = since_str.strip()
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    rel = re.fullmatch(r"(\d+)\s*[dD]", clean)
    if rel:
        days = int(rel.group(1))
        return now_dt - timedelta(days=days)

    dt = parse_iso(clean)
    if dt is None:
        raise ReportError(
            f"Invalid --since value '{since_str}'. Use YYYY-MM-DD (e.g. 2026-11-01) or Nd (e.g. 30d)."
        )
    return dt


def build_sparkline(values: List[int]) -> str:
    """Renders a compact Unicode block sparkline for non-negative counts."""
    if not values or max(values) <= 0:
        return SPARK_BLOCKS[0] * len(values)
    top = max(values)
    chars = []
    for v in values:
        idx = int(round((v / top) * (len(SPARK_BLOCKS) - 1)))
        idx = max(0, min(idx, len(SPARK_BLOCKS) - 1))
        chars.append(SPARK_BLOCKS[idx])
    return "".join(chars)


def _extract_reached_stages(current_stage: str, app_events: List[Dict[str, Any]]) -> set:
    """Determines all funnel stages an application reached based on events and current stage."""
    reached = {current_stage}
    for ev in app_events:
        if ev.get("kind") == "stage_change":
            detail = ev.get("detail", "").lower()
            for stage in FUNNEL_ORDER:
                if f"'{stage}'" in detail or f"-> {stage}" in detail or f"{stage} ->" in detail:
                    reached.add(stage)

    # Ensure implied prior stages when user logged directly at a later stage
    if "offer" in reached:
        reached.update({"saved", "applied", "screen", "interview"})
    elif "interview" in reached:
        reached.update({"saved", "applied", "screen"})
    elif "screen" in reached:
        reached.update({"saved", "applied"})
    elif current_stage in ("rejected", "ghosted") or "applied" in reached:
        reached.update({"saved", "applied"})
    return reached


def generate_report(
    store: CareerStore,
    since: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Computes pipeline funnel, response rates by CV SHA-256 and source, and average response days."""
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    since_dt = parse_since(since, now=now_dt)

    apps = store.list_applications()
    all_events = store.list_all_events()
    events_by_app: Dict[int, List[Dict[str, Any]]] = {}
    for ev in all_events:
        events_by_app.setdefault(int(ev["application_id"]), []).append(ev)

    filtered_apps: List[Dict[str, Any]] = []
    for app in apps:
        app_evs = events_by_app.get(int(app["id"]), [])
        anchor_dt = parse_iso(app.get("applied_at")) or (
            parse_iso(app_evs[0]["at"]) if app_evs else parse_iso(app.get("first_seen"))
        )
        if since_dt is not None and anchor_dt is not None and anchor_dt < since_dt:
            continue
        app_copy = dict(app)
        app_copy["_events"] = app_evs
        filtered_apps.append(app_copy)

    funnel_counts: Dict[str, int] = {st: 0 for st in FUNNEL_ORDER}
    current_stage_counts: Dict[str, int] = {
        st: 0 for st in (*FUNNEL_ORDER, "rejected", "ghosted")
    }

    by_cv: Dict[str, Dict[str, int]] = {}
    by_source: Dict[str, Dict[str, int]] = {}
    response_days: List[float] = []
    active_ages_days: List[float] = []

    for app in filtered_apps:
        stage = app["stage"]
        if stage in current_stage_counts:
            current_stage_counts[stage] += 1

        reached = _extract_reached_stages(stage, app["_events"])
        for st in FUNNEL_ORDER:
            if st in reached:
                funnel_counts[st] += 1

        ever_applied = "applied" in reached
        responded = any(st in reached for st in RESPONSE_STAGES)

        if ever_applied:
            cv_key = (app.get("cv_sha256") or "(none)")[:12]
            cv_entry = by_cv.setdefault(cv_key, {"applied": 0, "responded": 0, "offers": 0})
            cv_entry["applied"] += 1
            if responded:
                cv_entry["responded"] += 1
            if "offer" in reached:
                cv_entry["offers"] += 1

            src_key = app.get("source") or "Unknown"
            src_entry = by_source.setdefault(src_key, {"applied": 0, "responded": 0, "offers": 0})
            src_entry["applied"] += 1
            if responded:
                src_entry["responded"] += 1
            if "offer" in reached:
                src_entry["offers"] += 1

        applied_dt = parse_iso(app.get("applied_at"))
        if applied_dt is not None:
            if stage in ("applied", "screen", "interview"):
                active_ages_days.append(max(0.0, (now_dt - applied_dt).total_seconds() / 86400.0))

            first_resp_dt = None
            for ev in app["_events"]:
                if ev.get("kind") == "stage_change":
                    det = ev.get("detail", "").lower()
                    if any(f"-> {s}" in det for s in RESPONSE_STAGES):
                        first_resp_dt = parse_iso(ev.get("at"))
                        break
            if first_resp_dt is not None and first_resp_dt >= applied_dt:
                response_days.append((first_resp_dt - applied_dt).total_seconds() / 86400.0)

    funnel_steps: List[Dict[str, Any]] = []
    saved_total = funnel_counts["saved"]
    for idx, st in enumerate(FUNNEL_ORDER):
        count = funnel_counts[st]
        if idx == 0:
            step_conv = 100.0 if count > 0 else 0.0
        else:
            prev_count = funnel_counts[FUNNEL_ORDER[idx - 1]]
            step_conv = round((count / prev_count) * 100.0, 1) if prev_count > 0 else 0.0
        from_saved = round((count / saved_total) * 100.0, 1) if saved_total > 0 else 0.0
        funnel_steps.append(
            {
                "stage": st,
                "count": count,
                "step_conversion_pct": step_conv,
                "overall_pct": from_saved,
            }
        )

    cv_breakdown = [
        {
            "cv_hash": k,
            "applied": v["applied"],
            "responded": v["responded"],
            "response_rate_pct": round((v["responded"] / v["applied"]) * 100.0, 1)
            if v["applied"] > 0
            else 0.0,
            "offers": v["offers"],
        }
        for k, v in sorted(by_cv.items(), key=lambda item: (-item[1]["applied"], item[0]))
    ]

    source_breakdown = [
        {
            "source": k,
            "applied": v["applied"],
            "responded": v["responded"],
            "response_rate_pct": round((v["responded"] / v["applied"]) * 100.0, 1)
            if v["applied"] > 0
            else 0.0,
            "offers": v["offers"],
        }
        for k, v in sorted(by_source.items(), key=lambda item: (-item[1]["applied"], item[0]))
    ]

    total_apps = len(filtered_apps)
    total_applied = funnel_counts["applied"]
    sample_too_small = total_applied < 10

    warnings: List[str] = []
    if total_apps == 0:
        warnings.append("No applications match this filter yet. Run 'forge track add' first.")
    elif sample_too_small:
        warnings.append(
            f"Sample too small ({total_applied} applied < 10): conversion rates are high-variance estimates."
        )

    avg_resp_days = round(sum(response_days) / len(response_days), 1) if response_days else None
    avg_active_age = round(sum(active_ages_days) / len(active_ages_days), 1) if active_ages_days else None

    return {
        "total_applications": total_apps,
        "total_applied": total_applied,
        "since": since,
        "sample_too_small": sample_too_small,
        "warnings": warnings,
        "funnel": funnel_steps,
        "funnel_sparkline": build_sparkline([s["count"] for s in funnel_steps]),
        "current_stages": current_stage_counts,
        "by_cv_version": cv_breakdown,
        "by_source": source_breakdown,
        "avg_response_days": avg_resp_days,
        "avg_active_days": avg_active_age,
    }
