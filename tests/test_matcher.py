"""
Unit tests for the ATS Matcher and Skill Gap Analysis Engine.
"""

from careerforge.core.matcher import (
    compute_ats_match,
    extract_skills_from_profile,
    extract_skills_from_text,
    load_skills_ontology,
)


def test_load_skills_ontology():
    alias_map, cat_map = load_skills_ontology()
    assert len(alias_map) > 100, "Skills ontology should load 100+ aliases"
    assert alias_map.get("python") == "Python"
    assert alias_map.get("postgres") == "PostgreSQL"
    assert alias_map.get("powerbi") == "Power BI"


def test_extract_skills_from_text():
    alias_map, _ = load_skills_ontology()
    sample_text = (
        "Looking for a Senior Backend Engineer proficient in Python, FastAPI, and PostgreSQL. "
        "Experience with Docker, Kubernetes, and Kafka is a big plus."
    )
    detected = extract_skills_from_text(sample_text, alias_map)
    assert "Python" in detected
    assert "FastAPI" in detected
    assert "PostgreSQL" in detected
    assert "Docker" in detected
    assert "Kubernetes" in detected
    assert "Kafka" in detected


def test_extract_skills_from_profile():
    alias_map, _ = load_skills_ontology()
    profile = {
        "skills": {
            "languages": ["Python", "Go", "SQL"],
            "databases": ["PostgreSQL", "Redis"],
        },
        "summary": "Building scalable microservices with Docker.",
    }
    extracted = extract_skills_from_profile(profile, alias_map)
    assert "Python" in extracted
    assert "Go" in extracted
    assert "SQL" in extracted
    assert "PostgreSQL" in extracted
    assert "Redis" in extracted
    assert "Docker" in extracted


def test_compute_ats_match():
    profile = {
        "skills": {
            "languages": ["Python", "SQL"],
            "tools": ["Docker"],
        },
        "experience": [
            {
                "company": "Acme",
                "role": "Engineer",
                "bullets": ["Optimized PostgreSQL queries reducing latency by 30%."],
            }
        ],
    }

    jd_text = (
        "Requirements: Python, PostgreSQL, Docker, Kafka, and Kubernetes."
    )

    res = compute_ats_match(jd_text, profile)
    assert res["match_percentage"] > 0
    assert "Python" in res["matched_skills"]
    assert "PostgreSQL" in res["matched_skills"]
    assert "Docker" in res["matched_skills"]
    assert "Kafka" in res["missing_skills"]
    assert "Kubernetes" in res["missing_skills"]
