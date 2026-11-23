"""
Knapsack-inspired Offline CV Tailoring Engine.
Re-ranks and selects the most relevant experience bullets, projects, and skills
from a candidate's Master Profile to fit a specific Job Description.
Guarantees 100% honesty: never hallucinates, only prioritizes verified bullets.
"""

import copy
import re
from typing import Any, Dict, List, Tuple

from careerforge.core.matcher import (
    compute_ats_match,
    extract_skills_from_text,
    load_skills_ontology,
)


def _has_quantifiable_metrics(text: str) -> bool:
    """Checks if a bullet point contains measurable achievements (numbers, %, $, ms, x)."""
    # Matches patterns like 840ms, 210ms, 14,000, 35%, $1.2M, 10x, 99.9%
    pattern = r"(\b\d+[\d,\.]*\s*(%|\$|ms|s|x|k|m|users|records|req/s)?\b|\$\d+)"
    return bool(re.search(pattern, text, re.IGNORECASE))


def score_bullet(
    bullet_item: Any,
    jd_skills: set,
    jd_text: str,
    alias_map: Dict[str, str],
) -> float:
    """
    Computes a relevance score for an experience bullet:
    - 4.0 points per matching skill required by the JD
    - 2.0 points for quantifiable metrics (numbers, %, latency, scale)
    - 0.5 points for word-token overlap with the JD
    - Configured weight bonus (1 to 10 scale)
    """
    if isinstance(bullet_item, dict):
        text = bullet_item.get("text", "")
        explicit_skills = bullet_item.get("skills", [])
        weight = float(bullet_item.get("weight", 5.0))
    else:
        text = str(bullet_item)
        explicit_skills = []
        weight = 5.0

    # 1. Skill overlap
    detected_skills = extract_skills_from_text(text, alias_map)
    for s in explicit_skills:
        c_name = alias_map.get(str(s).strip().lower(), str(s).strip())
        detected_skills.add(c_name)

    matching_skills = detected_skills & jd_skills
    skill_score = len(matching_skills) * 4.0

    # 2. Metric bonus
    metric_score = 2.0 if _has_quantifiable_metrics(text) else 0.0

    # 3. Keyword / token overlap (excluding basic stopwords)
    stopwords = {"and", "the", "in", "with", "to", "for", "of", "a", "an", "on", "by", "as", "at"}
    bullet_tokens = {t.lower() for t in re.findall(r"\b\w{3,}\b", text)} - stopwords
    jd_tokens = {t.lower() for t in re.findall(r"\b\w{3,}\b", jd_text)} - stopwords
    token_overlap = len(bullet_tokens & jd_tokens) * 0.1

    # 4. Weight score (normalized to 0-1)
    weight_score = (weight / 10.0)

    total_score = skill_score + metric_score + token_overlap + weight_score
    return round(total_score, 2)


def tailor_profile(
    profile_data: Dict[str, Any],
    jd_text: str,
    max_bullets_per_role: int = 4,
    max_projects: int = 2,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Tailors a master profile for a specific job description.
    Returns:
    - tailored_profile: deep copy of profile with prioritized bullets and skills
    - report: detailed tailoring breakdown (matched skills, selected bullets, score delta)
    """
    alias_map, _cat_map = load_skills_ontology()
    initial_match = compute_ats_match(jd_text, profile_data)
    jd_skills = set(initial_match["matched_skills"]) | set(initial_match["missing_skills"])

    tailored = copy.deepcopy(profile_data)
    report_roles: List[Dict[str, Any]] = []

    # 1. Tailor Experiences
    for exp in tailored.get("experience", []):
        if not isinstance(exp, dict):
            continue
        company = exp.get("company", "Unknown")
        role = exp.get("title", "") or exp.get("role", "")
        raw_bullets = exp.get("bullets", [])

        scored_bullets = []
        for b in raw_bullets:
            b_text = b.get("text", "") if isinstance(b, dict) else str(b)
            score = score_bullet(b, jd_skills, jd_text, alias_map)
            scored_bullets.append((score, b_text, b))

        # Sort descending by score
        scored_bullets.sort(key=lambda x: x[0], reverse=True)

        # Select top bullets up to budget limit
        selected_raw = scored_bullets[:max_bullets_per_role]
        exp["bullets"] = [item[1] for item in selected_raw]

        report_roles.append({
            "company": company,
            "role": role,
            "total_available_bullets": len(raw_bullets),
            "selected_count": len(exp["bullets"]),
            "top_selected": [item[1] for item in selected_raw],
        })

    # 2. Tailor Projects (prioritize projects containing JD skills)
    projects = tailored.get("projects", [])
    if projects and isinstance(projects, list):
        scored_projects = []
        for p in projects:
            p_text = f"{p.get('name', '')} {p.get('description', '')}"
            p_skills = extract_skills_from_text(p_text, alias_map)
            p_overlap = len(p_skills & jd_skills)
            scored_projects.append((p_overlap, p))

        scored_projects.sort(key=lambda x: x[0], reverse=True)
        tailored["projects"] = [item[1] for item in scored_projects[:max_projects]]

    # 3. Prioritize Skills list
    # Sort category skills so that JD-matched skills appear first in the bullet lists
    skills_sec = tailored.get("skills", {})
    if isinstance(skills_sec, dict):
        for cat, items in skills_sec.items():
            if isinstance(items, list):
                # Separate items that match JD vs others
                matched_items = []
                other_items = []
                for item in items:
                    c_name = alias_map.get(str(item).strip().lower(), str(item).strip())
                    if c_name in jd_skills or str(item).strip() in jd_skills:
                        matched_items.append(item)
                    else:
                        other_items.append(item)
                skills_sec[cat] = matched_items + other_items

    # 4. Final verification match
    final_match = compute_ats_match(jd_text, tailored)

    report = {
        "initial_match_percentage": initial_match["match_percentage"],
        "tailored_match_percentage": final_match["match_percentage"],
        "matched_skills": final_match["matched_skills"],
        "missing_skills": final_match["missing_skills"],
        "total_jd_skills_detected": final_match["total_jd_skills"],
        "roles_tailored": report_roles,
    }

    return tailored, report
