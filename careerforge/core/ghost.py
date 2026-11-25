"""
Heuristic Ghost Job Risk Evaluator (`forge ghost`).
Analyzes stored jobs in SQLite using transparent, weighted signals.
Notice: outputs heuristic risk estimates, never proof of employer intent.
Zero network requests.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from careerforge.core.store import CareerStore, parse_iso
except ImportError:
    from core.store import CareerStore, parse_iso

GHOST_NOTICE = "Heuristic ghost risk estimate, not proof of employer intent."

WEIGHTS = {
    "AGE": 25,
    "REPOST": 25,
    "STALE_OR_CLOSED": 20,
    "VAGUE_JD": 15,
    "UNCHANGED_HASH": 15,
}

CONCRETE_JD_MARKERS = (
    "responsibilities",
    "requirements",
    "qualifications",
    "what you'll do",
    "what you will do",
    "experience",
    "skills",
    "tech stack",
)


def _norm_company_title(company: str, title: str) -> Tuple[str, str]:
    c = (company or "").strip().lower()
    t = re.sub(r"[^a-z0-9]", "", (title or "").lower())
    return c, t


def score_job_ghost_risk(
    job: Dict[str, Any],
    repost_counts: Dict[Tuple[str, str], int],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Computes heuristic Ghost Risk (Low/Medium/High, 0-100) and itemized reasons for one job.
    """
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    score = 0
    reasons: List[str] = []

    # 1. Posting age (up to 25)
    posted_dt = parse_iso(job.get("posted_at")) or parse_iso(job.get("first_seen"))
    age_days: Optional[int] = None
    if posted_dt is not None:
        age_days = max(0, int((now_dt - posted_dt).total_seconds() // 86400))
        if age_days >= 60:
            score += 25
            reasons.append(f"Posting age is {age_days} days (>= 60d old, +25).")
        elif age_days >= 30:
            score += 15
            reasons.append(f"Posting age is {age_days} days (>= 30d old, +15).")

    # 2. Repost count across same company + normalized title (up to 25)
    key = _norm_company_title(job.get("company", ""), job.get("title", ""))
    repost_count = repost_counts.get(key, 1)
    if repost_count >= 3:
        score += 25
        reasons.append(f"Same company and title appears {repost_count} times in DB (+25).")
    elif repost_count == 2:
        score += 15
        reasons.append("Same company and title appears 2 times in DB (+15).")

    # 3. Closed or stale last_seen visibility (up to 20)
    last_seen_dt = parse_iso(job.get("last_seen"))
    if job.get("closed_at"):
        score += 20
        reasons.append(f"Posting marked closed at {str(job['closed_at'])[:10]} (+20).")
    elif last_seen_dt is not None:
        stale_gap = max(0, int((now_dt - last_seen_dt).total_seconds() // 86400))
        if stale_gap >= 14:
            score += 10
            reasons.append(f"Not refreshed in {stale_gap} days since last_seen (+10).")

    # 4. Vague JD signal (no salary + short/missing responsibility details) (up to 15)
    has_salary = job.get("salary_min") is not None or job.get("salary_max") is not None
    desc = (job.get("description") or "").strip()
    desc_low = desc.lower()
    has_scope = any(m in desc_low for m in CONCRETE_JD_MARKERS)

    if not has_salary and (len(desc) < 120 or not has_scope):
        if len(desc) < 120:
            score += 15
            reasons.append("No salary range and missing/short (<120 chars) job description (+15).")
        else:
            score += 8
            reasons.append("No salary range and lacks explicit requirement/responsibility markers (+8).")

    # 5. Unchanged description hash over extended window (up to 15)
    desc_hash = job.get("description_hash") or (
        hashlib.sha256(desc.encode("utf-8")).hexdigest()[:16] if desc else ""
    )
    changed_dt = parse_iso(job.get("description_changed_at")) or parse_iso(job.get("first_seen"))
    if desc_hash and changed_dt is not None and last_seen_dt is not None:
        unchanged_days = max(0, int((last_seen_dt - changed_dt).total_seconds() // 86400))
        if unchanged_days >= 30:
            score += 15
            reasons.append(
                f"Description hash ({desc_hash[:8]}) unchanged across {unchanged_days} days (+15)."
            )
        elif unchanged_days >= 14:
            score += 8
            reasons.append(
                f"Description hash ({desc_hash[:8]}) unchanged across {unchanged_days} days (+8)."
            )

    score = min(100, score)
    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "job_id": job["id"],
        "company": job.get("company", ""),
        "title": job.get("title", ""),
        "source": job.get("source", ""),
        "url": job.get("url", ""),
        "risk_score": score,
        "risk_level": level,
        "age_days": age_days,
        "repost_count": repost_count,
        "closed": bool(job.get("closed_at")),
        "reasons": reasons or ["No elevated ghost signals detected."],
        "notice": GHOST_NOTICE,
    }


def analyze_ghost_jobs(
    store: CareerStore,
    job_id: Optional[Any] = None,
    top: int = 20,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Evaluates one job (by ID/external_id/hash) or returns top ranked ghost-risk jobs."""
    all_jobs = store.list_jobs(limit=None, include_closed=True)

    repost_counts: Dict[Tuple[str, str], int] = {}
    for j in all_jobs:
        k = _norm_company_title(j.get("company", ""), j.get("title", ""))
        repost_counts[k] = repost_counts.get(k, 0) + 1

    if job_id is not None:
        target = store.get_job(job_id)
        if target is None:
            raise ValueError(f"Job not found: '{job_id}'")
        item = score_job_ghost_risk(target, repost_counts, now=now)
        return {
            "heuristic": True,
            "notice": GHOST_NOTICE,
            "count": 1,
            "items": [item],
        }

    scored = [score_job_ghost_risk(j, repost_counts, now=now) for j in all_jobs]
    scored.sort(key=lambda x: (-x["risk_score"], -x["repost_count"], x["job_id"]))

    return {
        "heuristic": True,
        "notice": GHOST_NOTICE,
        "count": len(scored[:top]),
        "total_jobs_evaluated": len(all_jobs),
        "items": scored[:top],
    }
