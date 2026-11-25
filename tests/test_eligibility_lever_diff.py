"""
Tests for remote geo-eligibility rules, false-positive guards, Lever scraper contract,
and `forge tailor --diff` itemized score breakdown.
"""

import json
import os
import sys
from unittest.mock import MagicMock

import pytest

from careerforge.cli import main
from careerforge.core.eligibility import check_eligibility, load_eligibility_rules
from careerforge.core.tailor_engine import tailor_profile
from careerforge.scrapers.board_registry import LEVER_BOARDS
from careerforge.scrapers.lever_scanner import LeverScraper


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["forge"] + argv)
    with pytest.raises(SystemExit) as exc:
        try:
            main()
        except SystemExit:
            raise
        else:
            raise SystemExit(0)
    return exc.value.code


def test_eligibility_rules_schema_and_positive_cases(socket_disabled=None):
    rules, guards = load_eligibility_rules()
    assert len(rules) >= 8
    assert len(guards) >= 3
    for r in rules:
        assert {"id", "regex", "region", "severity", "notes"} <= set(r.keys())

    # Positive US residency + worldwide override -> Restricted takes priority
    jd_us = (
        "We are a remote-first worldwide distributed company. "
        "However, applicants must be located in the United States and authorized to work in the US."
    )
    res_bd = check_eligibility(jd_us, my_country="BD")
    assert res_bd["heuristic"] is True
    assert res_bd["status"] == "Restricted"
    assert "US" in res_bd["regions"]
    assert res_bd["can_apply"]["eligible"] is False
    assert len(res_bd["evidence"]) >= 1

    # Same US job evaluated with --my-country US -> eligible!
    res_us = check_eligibility(jd_us, my_country="US")
    assert res_us["status"] == "Restricted"
    assert res_us["can_apply"]["eligible"] is True

    # Visa + Timezone likely restricted
    jd_tz = "Remote role requiring EST working hours overlap. No visa sponsorship is available."
    res_tz = check_eligibility(jd_tz, my_country="BD")
    assert res_tz["status"] == "Likely restricted"
    assert "VISA_RESTRICTED" in res_tz["regions"]
    assert "AMERICAS_TZ" in res_tz["regions"]


def test_eligibility_negative_false_positive_guards(socket_disabled=None):
    """Company office descriptions must NOT trigger false geo-restrictions."""
    jd_clean = (
        "Our engineering team is located in San Francisco and our headquarters are in London. "
        "You can work from anywhere across the globe with flexible async hours."
    )
    res = check_eligibility(jd_clean, my_country="BD")
    assert res["status"] == "Eligible"
    assert res["evidence"] == []
    assert res["can_apply"]["eligible"] is True


def test_lever_scraper_contract_offline_fixture(socket_disabled=None):
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "lever_sample.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture_data = json.load(f)

    assert len(LEVER_BOARDS) >= 5
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fixture_data
    mock_session.get.return_value = mock_resp

    scraper = LeverScraper(session=mock_session, boards=["kinsta"])
    postings, ok_boards, failed = scraper.fetch_with_status(
        {"keywords": ["Data Analyst"], "exclude_senior": True}
    )

    assert ("Lever", "Kinsta") in ok_boards
    assert failed == []
    assert len(postings) == 1
    p = postings[0]
    assert p.source == "Lever"
    assert p.company == "Kinsta"
    assert p.salary_min == 65000.0
    assert p.salary_max == 85000.0
    assert p.currency == "USD"
    assert p.remote_policy == "Remote"
    assert p.posted_at is not None


def test_tailor_diff_bullet_counts_match_tailor(tmp_path, monkeypatch, capsys, socket_disabled=None):
    profile = {
        "personal": {"full_name": "Alex Rivera", "email": "alex@example.com"},
        "skills": {"backend": ["Python", "PostgreSQL", "Redis"]},
        "experience": [
            {
                "company": "Apex",
                "title": "Engineer",
                "bullets": [
                    {"text": "Tuned PostgreSQL queries cutting latency by 40%.", "skills": ["PostgreSQL"], "weight": 8},
                    {"text": "Managed Redis caching layer for Python API.", "skills": ["Redis", "Python"], "weight": 8},
                    {"text": "Attended sprint retrospectives.", "skills": [], "weight": 3},
                ],
            }
        ],
        "education": [{"institution": "UT", "degree": "BS"}],
    }
    jd = "Looking for a Python and PostgreSQL engineer."
    tailored_prof, report = tailor_profile(profile, jd, max_bullets_per_role=2)

    role_rep = report["roles_tailored"][0]
    selected_diffs = [d for d in role_rep["bullet_diffs"] if d["selected"]]
    dropped_diffs = [d for d in role_rep["bullet_diffs"] if not d["selected"]]

    assert len(selected_diffs) == len(tailored_prof["experience"][0]["bullets"]) == 2
    assert len(dropped_diffs) == 1
    assert dropped_diffs[0]["text"] == "Attended sprint retrospectives."
    assert all("skill_score" in d and "total_score" in d for d in role_rep["bullet_diffs"])

    # CLI check for eligibility --json and match --my-country
    assert _run_cli(["eligibility", "--jd", "Must reside in Canada.", "--my-country", "BD", "--json"], monkeypatch) == 0
    elig_json = json.loads(capsys.readouterr().out)
    assert elig_json["status"] == "Restricted"
    assert elig_json["can_apply"]["eligible"] is False
