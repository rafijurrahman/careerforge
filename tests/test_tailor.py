"""
Unit tests for the Knapsack CV Tailoring Engine.
"""

from careerforge.core.matcher import load_skills_ontology
from careerforge.core.tailor_engine import (
    _has_quantifiable_metrics,
    score_bullet,
    tailor_profile,
)


def test_has_quantifiable_metrics():
    assert _has_quantifiable_metrics("Reduced latency from 840ms to 210ms.")
    assert _has_quantifiable_metrics("Cut cloud infrastructure costs by 35%.")
    assert _has_quantifiable_metrics("Managed cluster handling 14,000 requests per second.")
    assert _has_quantifiable_metrics("Saved $18,000 annually.")
    assert not _has_quantifiable_metrics("Collaborated with teams on system design.")


def test_score_bullet():
    alias_map, _ = load_skills_ontology()
    jd_skills = {"Redis", "PostgreSQL", "Kafka"}
    jd_text = "Looking for Kafka and Redis experts with proven database optimization experience."

    b1 = {
        "text": "Introduced Redis caching cutting p95 response time by 45%.",
        "skills": ["Redis"],
        "weight": 9,
    }
    b2 = {
        "text": "Attended daily engineering standups and drafted Jira tickets.",
        "skills": [],
        "weight": 3,
    }

    s1 = score_bullet(b1, jd_skills, jd_text, alias_map)
    s2 = score_bullet(b2, jd_skills, jd_text, alias_map)

    assert s1 > s2, f"Targeted bullet ({s1}) should score substantially higher than generic bullet ({s2})"


def test_tailor_profile():
    profile = {
        "personal": {"full_name": "Test Candidate"},
        "skills": {
            "languages": ["Python", "JavaScript", "Go"],
            "data": ["PostgreSQL", "MongoDB", "Redis"],
        },
        "experience": [
            {
                "company": "Acme",
                "role": "Backend Engineer",
                "bullets": [
                    {
                        "text": "Architected event streaming in Go and Kafka handling 10k msg/s.",
                        "skills": ["Kafka", "Go"],
                        "weight": 9,
                    },
                    {
                        "text": "Built frontend forms using JavaScript and React.",
                        "skills": ["JavaScript"],
                        "weight": 5,
                    },
                    {
                        "text": "Optimized PostgreSQL indexes reducing query duration by 30%.",
                        "skills": ["PostgreSQL"],
                        "weight": 8,
                    },
                ],
            }
        ],
    }

    jd_text = "Requirements: High-throughput Kafka and PostgreSQL pipeline engineering."

    tailored, report = tailor_profile(profile, jd_text, max_bullets_per_role=2)

    exp_bullets = tailored["experience"][0]["bullets"]
    assert len(exp_bullets) == 2, "Should select top 2 bullets per budget"

    # Kafka and PostgreSQL bullets should be chosen over JavaScript
    assert any("Kafka" in b for b in exp_bullets)
    assert any("PostgreSQL" in b for b in exp_bullets)
    assert not any("JavaScript" in b for b in exp_bullets)

    assert report["tailored_match_percentage"] > 0
    assert "Kafka" in report["matched_skills"]
    assert "PostgreSQL" in report["matched_skills"]
