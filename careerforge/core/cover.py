"""
Offline Template-Based Cover Letter & Outreach Generator for CareerForge.
Builds 'hook -> proof -> ask' drafts from profile.yaml + JD skill matching
without cloud LLMs, inserts explicit '<<FILL: ...>>' markers for unknown
slots, enforces strict word/character caps, integrates with CareerStore for
follow-ups, and automatically audits drafts with Anti-AI heuristics.
"""

from __future__ import annotations

import os
import re
from importlib import resources
from typing import Any, Dict, List, Optional, Tuple

try:
    from careerforge.core.anti_ai_engine import audit_text
    from careerforge.core.matcher import (
        compute_ats_match,
        extract_skills_from_profile,
        extract_skills_from_text,
        load_skills_ontology,
    )
    from careerforge.core.tailor_engine import score_bullet_breakdown
except ImportError:
    from core.anti_ai_engine import audit_text
    from core.matcher import (
        compute_ats_match,
        extract_skills_from_profile,
        extract_skills_from_text,
        load_skills_ontology,
    )
    from core.tailor_engine import score_bullet_breakdown

VALID_OUTREACH_TYPES: Tuple[str, ...] = ("cover", "cold-email", "linkedin", "follow-up")

TEMPLATE_FILES: Dict[str, str] = {
    "cover": "cover.txt",
    "cold-email": "cold_email.txt",
    "linkedin": "linkedin.txt",
    "follow-up": "follow_up.txt",
}

FILL_PATTERN = re.compile(r"<<FILL:[^>]+>>")


class CoverError(Exception):
    """Raised on invalid template type, missing tracked application, or bad inputs."""


def load_template(doc_type: str) -> str:
    """Loads a packaged plain-text outreach template."""
    key = (doc_type or "cover").strip().lower()
    if key not in VALID_OUTREACH_TYPES:
        raise CoverError(
            f"Unsupported outreach type '{doc_type}'. Choose from: {', '.join(VALID_OUTREACH_TYPES)}."
        )
    filename = TEMPLATE_FILES[key]
    try:
        tpl_ref = resources.files("careerforge.data").joinpath("templates", filename)
        return tpl_ref.read_text(encoding="utf-8")
    except Exception:
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "templates",
            filename,
        )
        if not os.path.exists(local_path):
            raise CoverError(f"Template file '{filename}' not found.")
        with open(local_path, "r", encoding="utf-8") as f:
            return f.read()


def _extract_jd_field(jd_text: str, labels: Tuple[str, ...]) -> Optional[str]:
    if not jd_text:
        return None
    for line in jd_text.splitlines():
        stripped = line.strip()
        for label in labels:
            m = re.match(rf"^{re.escape(label)}\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val:
                    return val
    return None


def _clean_bullet_sentence(bullet: Any) -> str:
    if isinstance(bullet, dict):
        body = str(bullet.get("text") or "").strip()
        prefix = str(bullet.get("bold_prefix") or "").strip()
        text = body or prefix
    else:
        text = str(bullet or "").strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _select_proof_items(
    profile_data: Dict[str, Any],
    jd_text: str,
    alias_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Selects and ranks proof sentences from profile experience and projects."""
    jd_skills = extract_skills_from_text(jd_text or "", alias_map)
    scored: List[Dict[str, Any]] = []

    experiences = profile_data.get("work_experience") or profile_data.get("experience") or []
    for idx, exp in enumerate(experiences):
        if not isinstance(exp, dict):
            continue
        company = str(exp.get("company") or "").strip()
        for b_idx, b in enumerate(exp.get("bullets") or []):
            sentence = _clean_bullet_sentence(b)
            if not sentence:
                continue
            bd = score_bullet_breakdown(b, jd_skills, jd_text or "", alias_map)
            scored.append(
                {
                    "text": sentence,
                    "source": company or "Experience",
                    "has_metric": bd["metric_score"] > 0,
                    "total_score": bd["total_score"],
                    "order": (idx * 100) + b_idx,
                }
            )

    projects = profile_data.get("featured_projects") or profile_data.get("projects") or []
    for p_idx, proj in enumerate(projects):
        if not isinstance(proj, dict):
            continue
        title = str(proj.get("title") or proj.get("name") or "").strip()
        desc = _clean_bullet_sentence(proj.get("description") or "")
        if not desc:
            continue
        bd = score_bullet_breakdown(desc, jd_skills, jd_text or "", alias_map)
        text = f"In my {title} project, I {desc[0].lower()}{desc[1:]}" if title else desc
        scored.append(
            {
                "text": text,
                "source": title or "Project",
                "has_metric": bd["metric_score"] > 0,
                "total_score": bd["total_score"] - 0.5,
                "order": 10000 + p_idx,
            }
        )

    scored.sort(key=lambda x: (x["has_metric"], x["total_score"], -x["order"]), reverse=True)
    return scored


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    clipped = " ".join(words[:max_words]).rstrip(",;:")
    if clipped and clipped[-1] not in ".!?":
        clipped += "."
    return clipped


def _truncate_chars(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    cut = text[: max_chars - 3].rsplit(" ", 1)[0].rstrip(",;:")
    return (cut or text[: max_chars - 3]) + "..."


def _count_words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def _format_candidate_links(personal: Dict[str, Any]) -> str:
    links: List[str] = []
    for key in ("email", "linkedin", "github", "portfolio"):
        val = str(personal.get(key) or "").strip()
        if val:
            links.append(val)
    return " | ".join(links[:3]) if links else "<<FILL: contact email or portfolio URL>>"


def generate_outreach(
    profile_data: Dict[str, Any],
    jd_text: str = "",
    doc_type: str = "cover",
    company: Optional[str] = None,
    role: Optional[str] = None,
    hiring_manager: Optional[str] = None,
    app_record: Optional[Dict[str, Any]] = None,
    jd_focus_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates an offline outreach draft using a static 'hook -> proof -> ask'
    template, real metrics from profile.yaml, '<<FILL: ...>>' markers for
    missing context, word/character limits, and automatic Anti-AI audit.
    """
    key = (doc_type or "cover").strip().lower()
    if key not in VALID_OUTREACH_TYPES:
        raise CoverError(
            f"Unsupported outreach type '{doc_type}'. Choose from: {', '.join(VALID_OUTREACH_TYPES)}."
        )

    effective_jd = (jd_text or "").strip()
    if not effective_jd and app_record and app_record.get("jd_snapshot"):
        effective_jd = str(app_record["jd_snapshot"]).strip()

    personal = profile_data.get("personal") or {}
    candidate_name = str(personal.get("full_name") or "").strip() or "<<FILL: your name>>"
    candidate_links = _format_candidate_links(personal)

    resolved_company = (
        (company or "").strip()
        or (str(app_record.get("company") or "").strip() if app_record else "")
        or (_extract_jd_field(effective_jd, ("Company", "Organization")) or "")
        or "<<FILL: company name>>"
    )
    resolved_role = (
        (role or "").strip()
        or (str(app_record.get("title") or "").strip() if app_record else "")
        or (_extract_jd_field(effective_jd, ("Role", "Title", "Position", "Job Title")) or "")
        or "<<FILL: role title>>"
    )
    resolved_hm = (hiring_manager or "").strip() or "<<FILL: hiring manager name>>"

    applied_date = "<<FILL: date applied>>"
    if app_record and app_record.get("applied_at"):
        applied_date = str(app_record["applied_at"])[:10]

    alias_map, _canon_map = load_skills_ontology()
    match_info = compute_ats_match(effective_jd, profile_data) if effective_jd else {}
    matched_list = list(match_info.get("matched_skills") or [])
    if not matched_list:
        matched_list = sorted(extract_skills_from_profile(profile_data, alias_map))[:5]

    matched_skills_str = ", ".join(matched_list[:5]) if matched_list else "<<FILL: relevant core skills>>"

    if jd_focus_override and jd_focus_override.strip():
        jd_focus = jd_focus_override.strip()
    elif matched_list:
        jd_focus = ", ".join(matched_list[:3])
    else:
        jd_focus = "<<FILL: specific team problem or stack focus>>"

    proofs = _select_proof_items(profile_data, effective_jd, alias_map)
    proof_primary = proofs[0]["text"] if proofs else "<<FILL: concrete work outcome with numbers>>"
    proof_second = proofs[1]["text"] if len(proofs) > 1 else ""
    extra_note = (
        "My projects follow simple rules: small test cycles, explicit data checks, "
        "clear metrics, and systems other engineers can debug quickly. "
        "If anything looks unclear in a service or table, I trace it to the schema before patching downstream code."
    )

    tpl = load_template(key)

    def _render(p1: str, p2: str, note: str, skills_s: str, compact_p: str) -> str:
        raw = tpl.format(
            hiring_manager=resolved_hm,
            role=resolved_role,
            company=resolved_company,
            jd_focus=jd_focus,
            proof=p1,
            proof_second=p2,
            matched_skills=skills_s,
            extra_note=note,
            candidate_name=candidate_name,
            candidate_links=candidate_links,
            applied_date=applied_date,
            compact_proof=compact_p,
        )
        # Clean whitespace around optional empty paragraphs
        lines = [ln.rstrip() for ln in raw.splitlines()]
        cleaned: List[str] = []
        for ln in lines:
            if not ln and cleaned and not cleaned[-1]:
                continue
            cleaned.append(ln)
        return "\n".join(cleaned).strip() + "\n"

    if key == "cover":
        rendered = _render(proof_primary, proof_second, extra_note, matched_skills_str, "")
        if _count_words(rendered) > 200:
            rendered = _render(proof_primary, proof_second, "", matched_skills_str, "")
        if _count_words(rendered) > 200:
            rendered = _render(proof_primary, "", "", matched_skills_str, "")
        if _count_words(rendered) > 200:
            excess = _count_words(rendered) - 196
            target_p1_words = max(12, _count_words(proof_primary) - excess)
            rendered = _render(_truncate_words(proof_primary, target_p1_words), "", "", ", ".join(matched_list[:3]) or matched_skills_str, "")
    elif key == "cold-email":
        rendered = _render(proof_primary, "", "", ", ".join(matched_list[:4]) or matched_skills_str, "")
        if _count_words(rendered) > 115:
            excess = _count_words(rendered) - 110
            target_words = max(12, _count_words(proof_primary) - excess)
            rendered = _render(_truncate_words(proof_primary, target_words), "", "", ", ".join(matched_list[:3]) or matched_skills_str, "")
    elif key == "linkedin":
        compact = proof_primary
        rendered = _render("", "", "", "", compact)
        if len(rendered.strip()) > 300:
            overhead = len(_render("", "", "", "", "").strip())
            budget = max(25, 295 - overhead)
            rendered = _render("", "", "", "", _truncate_chars(proof_primary, budget))
    else:  # follow-up
        rendered = _render(proof_primary, "", "", matched_skills_str, "")
        if _count_words(rendered) > 125:
            excess = _count_words(rendered) - 120
            target_words = max(12, _count_words(proof_primary) - excess)
            rendered = _render(_truncate_words(proof_primary, target_words), "", "", matched_skills_str, "")

    fill_markers = FILL_PATTERN.findall(rendered)
    audit_result = audit_text(rendered)

    return {
        "type": key,
        "company": resolved_company,
        "role": resolved_role,
        "hiring_manager": resolved_hm,
        "applied_date": applied_date if key == "follow-up" else None,
        "app_id": app_record.get("id") if app_record else None,
        "word_count": _count_words(rendered),
        "char_count": len(rendered.strip()),
        "fill_markers": fill_markers,
        "matched_skills": matched_list[:5],
        "selected_proofs": [p["text"] for p in proofs[: (2 if key == "cover" else 1)]],
        "audit": audit_result,
        "text": rendered,
    }
