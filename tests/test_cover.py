"""Tests for CareerForge template outreach & cover letter generator (PR 5)."""

from __future__ import annotations

import json
import os
import sys

import pytest

from careerforge import cli
from careerforge.core.anti_ai_engine import audit_text
from careerforge.core.cover import (
    VALID_OUTREACH_TYPES,
    CoverError,
    generate_outreach,
    load_template,
)
from careerforge.core.profile_loader import load_profile
from careerforge.core.store import CareerStore


def _example_profile_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "examples", "profile.example.yaml")


SAMPLE_JD = """
Backend & Data Platform Engineer
Looking for someone experienced in Python, PostgreSQL, Docker, FastAPI, and REST API optimization.
"""


def test_raw_templates_pass_anti_ai_audit():
    sample_values = {
        "hiring_manager": "Sam Lee",
        "role": "Backend Engineer",
        "company": "Northwind",
        "jd_focus": "Python and PostgreSQL",
        "proof": "Built 8 FastAPI microservices serving 2.5M daily requests under 50ms latency.",
        "proof_second": "Refactored PostgreSQL indexes and cut query response time by 42%.",
        "matched_skills": "Python, PostgreSQL, Docker",
        "extra_note": "My projects follow simple rules: small test cycles and explicit data checks.",
        "candidate_name": "Alex Rivera",
        "candidate_links": "alex@example.com | https://github.com/alex",
        "applied_date": "2026-11-10",
        "compact_proof": "Built 8 FastAPI microservices serving 2.5M req/day.",
    }
    for t in VALID_OUTREACH_TYPES:
        raw = load_template(t)
        rendered = raw.format(**sample_values)
        res = audit_text(rendered)
        assert res["compliant"] is True, f"Template '{t}' failed Anti-AI audit: {res['findings']}"
        assert res["total_issues"] == 0, f"Template '{t}' triggered findings: {res['findings']}"


def test_cover_word_limits_and_fill_markers():
    profile = load_profile(_example_profile_path())

    cover = generate_outreach(profile, jd_text=SAMPLE_JD, doc_type="cover")
    assert 150 <= cover["word_count"] <= 200
    assert "<<FILL: hiring manager name>>" in cover["fill_markers"]
    assert "<<FILL: company name>>" in cover["fill_markers"]
    assert "<<FILL: role title>>" in cover["fill_markers"]
    assert cover["audit"]["compliant"] is True

    email = generate_outreach(
        profile,
        jd_text=SAMPLE_JD,
        doc_type="cold-email",
        company="Northwind",
        role="Backend Engineer",
        hiring_manager="Jordan",
    )
    assert email["word_count"] <= 115
    assert email["fill_markers"] == []
    assert email["audit"]["compliant"] is True

    li = generate_outreach(
        profile,
        jd_text=SAMPLE_JD,
        doc_type="linkedin",
        company="Northwind",
        role="Backend Engineer",
        hiring_manager="Jordan",
    )
    assert li["char_count"] <= 300
    assert li["word_count"] <= 80
    assert li["audit"]["compliant"] is True

    with pytest.raises(CoverError):
        generate_outreach(profile, jd_text=SAMPLE_JD, doc_type="tweet")


def test_cover_followup_reads_tracked_application(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "cf.db")
    monkeypatch.setenv("CAREERFORGE_DB", db_path)
    store = CareerStore(db_path=db_path)
    app = store.add_application(
        url="https://example.com/jobs/101",
        company="Northwind Labs",
        title="Backend Engineer",
        stage="applied",
        jd_snapshot=SAMPLE_JD,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "forge",
            "cover",
            "--type",
            "follow-up",
            "--app",
            str(app["id"]),
            "--profile",
            _example_profile_path(),
            "--json",
        ],
    )
    cli.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["app_id"] == app["id"]
    assert payload["company"] == "Northwind Labs"
    assert payload["role"] == "Backend Engineer"
    assert payload["applied_date"] is not None
    assert "<<FILL: hiring manager name>>" in payload["fill_markers"]
    assert payload["audit"]["compliant"] is True


def test_cli_cover_missing_profile_exits_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["forge", "cover", "--jd", "Need SQL and Python"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert "forge init" in capsys.readouterr().err
