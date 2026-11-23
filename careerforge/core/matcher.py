"""
ATS Skill Matcher & Keyword Gap Analysis Engine.
Offline, deterministic matching using careerforge/data/skills.yaml ontology.
Zero network access, zero cloud telemetry, zero LLM hallucination.
"""

import os
import re
from typing import Any, Dict, Set, Tuple

import yaml

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources


def load_skills_ontology() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Loads skills.yaml from package data and builds lookup dictionaries:
    - alias_to_canonical: maps lowercase aliases and canonical names to Canonical Name
    - canonical_to_category: maps Canonical Name to category
    """
    data = {}
    try:
        ref = resources.files("careerforge.data").joinpath("skills.yaml")
        with ref.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        local_path = os.path.join(os.path.dirname(__file__), "..", "data", "skills.yaml")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

    alias_to_canonical: Dict[str, str] = {}
    canonical_to_category: Dict[str, str] = {}

    for category, skills in data.items():
        if not isinstance(skills, dict):
            continue
        for _skill_key, info in skills.items():
            if not isinstance(info, dict):
                continue
            canonical = info.get("canonical")
            if not canonical:
                continue

            canonical_to_category[canonical] = category

            # Map canonical name itself
            alias_to_canonical[canonical.lower()] = canonical

            # Map all aliases
            aliases = info.get("aliases", [])
            for alias in aliases:
                if alias:
                    alias_to_canonical[str(alias).strip().lower()] = canonical

    return alias_to_canonical, canonical_to_category


def extract_skills_from_text(text: str, alias_map: Dict[str, str]) -> Set[str]:
    """
    Extracts all canonical skills present in the given text.
    Handles single-word, multi-word, and special symbols (C++, C#, .NET).
    """
    if not text:
        return set()

    found: Set[str] = set()

    # Sort aliases by length descending so longer phrases match first (e.g. "Power BI" before "BI")
    sorted_aliases = sorted(alias_map.keys(), key=lambda x: len(x), reverse=True)

    for alias in sorted_aliases:
        escaped = re.escape(alias)
        if re.search(r"\w$", alias):
            if re.search(r"^\w", alias):
                pattern = rf"\b{escaped}\b"
            else:
                pattern = rf"(?<!\w){escaped}\b"
        else:
            pattern = rf"(?<!\w){escaped}(?!\+)"

        if re.search(pattern, text, re.IGNORECASE):
            canonical = alias_map[alias]
            found.add(canonical)

    return found


def extract_skills_from_profile(profile_data: Dict[str, Any], alias_map: Dict[str, str]) -> Set[str]:
    """
    Extracts all skills from a profile:
    1. Explicit skills listed under 'skills' section
    2. Skills mentioned in summary, experience bullets, and projects
    """
    profile_skills: Set[str] = set()

    # 1. Parse explicit skills section
    skills_sec = profile_data.get("skills", {})
    if isinstance(skills_sec, dict):
        for _cat, items in skills_sec.items():
            if isinstance(items, list):
                for item in items:
                    c_name = alias_map.get(str(item).strip().lower(), str(item).strip())
                    profile_skills.add(c_name)
            elif isinstance(items, str):
                for token in items.split(","):
                    c_name = alias_map.get(token.strip().lower(), token.strip())
                    profile_skills.add(c_name)
    elif isinstance(skills_sec, list):
        for item in skills_sec:
            c_name = alias_map.get(str(item).strip().lower(), str(item).strip())
            profile_skills.add(c_name)

    # 2. Extract skills from summary
    summary_text = profile_data.get("summary", "") or profile_data.get("professional_summary", "")
    if summary_text:
        profile_skills.update(extract_skills_from_text(summary_text, alias_map))

    # 3. Extract skills from experiences and bullets
    for exp in profile_data.get("experience", []):
        if not isinstance(exp, dict):
            continue
        title = exp.get("title", "") or exp.get("role", "")
        profile_skills.update(extract_skills_from_text(title, alias_map))

        bullets = exp.get("bullets", [])
        for b in bullets:
            if isinstance(b, dict):
                text = b.get("text", "")
                profile_skills.update(extract_skills_from_text(text, alias_map))
                for s in b.get("skills", []):
                    c_name = alias_map.get(str(s).strip().lower(), str(s).strip())
                    profile_skills.add(c_name)
            elif isinstance(b, str):
                profile_skills.update(extract_skills_from_text(b, alias_map))

    # 4. Extract skills from projects
    for proj in profile_data.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj_text = f"{proj.get('name', '')} {proj.get('description', '')}"
        profile_skills.update(extract_skills_from_text(proj_text, alias_map))
        for s in proj.get("skills", []):
            c_name = alias_map.get(str(s).strip().lower(), str(s).strip())
            profile_skills.add(c_name)

    return profile_skills


def compute_ats_match(jd_text: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes an ATS keyword gap analysis between a Job Description and a Candidate Profile.
    Returns:
    - match_percentage: float (0.0 to 100.0)
    - matched_skills: list of skills both in JD and profile
    - missing_skills: list of skills required by JD but absent in profile
    - additional_skills: profile skills not mentioned in JD
    - total_jd_skills: count of detected JD skills
    """
    alias_map, _cat_map = load_skills_ontology()

    jd_skills = extract_skills_from_text(jd_text, alias_map)
    profile_skills = extract_skills_from_profile(profile_data, alias_map)

    matched = jd_skills & profile_skills
    missing = jd_skills - profile_skills
    additional = profile_skills - jd_skills

    if jd_skills:
        score = round((len(matched) / len(jd_skills)) * 100.0, 1)
    else:
        score = 100.0

    return {
        "match_percentage": score,
        "matched_skills": sorted(list(matched)),
        "missing_skills": sorted(list(missing)),
        "additional_skills": sorted(list(additional)),
        "total_jd_skills": len(jd_skills),
        "matched_count": len(matched),
        "missing_count": len(missing),
    }
