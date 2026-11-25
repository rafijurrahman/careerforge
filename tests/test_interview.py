"""Tests for CareerForge interview preparation (PR 4: feat/interview-star)."""

from __future__ import annotations

import json
import os
import sys

import pytest

from careerforge import cli
from careerforge.core.interview import (
    STAR_CATEGORIES,
    TODO_PLACEHOLDER,
    VALID_ROLES,
    InterviewError,
    StoryBank,
    draft_stories_from_profile,
    load_questions,
    select_practice_questions,
)


def _sample_profile():
    return {
        "personal": {"full_name": "Alex Rivera"},
        "work_experience": [
            {
                "title": "Data Analyst",
                "company": "Northwind Logistics",
                "duration": "2023 - Present",
                "location": "Remote",
                "bullets": [
                    "Maintained weekly team documentation and sprint notes.",
                    "Automated SQL reporting pipelines, cutting run time by 45% across 120k rows.",
                ],
            }
        ],
        "featured_projects": [
            {
                "title": "FreightDelay Monitor",
                "tech_stack": "Python, SQLite",
                "description": "Tracked 15 regional hubs with zero external telemetry.",
            }
        ],
        "academic_background": [{"degree": "B.S. Statistics", "institution": "State University"}],
    }


def test_draft_stories_honesty_and_metric_priority():
    drafts = draft_stories_from_profile(_sample_profile(), limit=10)
    assert len(drafts) == 3

    # Metric-bearing items rank before plain descriptive bullet
    assert drafts[0]["has_metric"] is True
    assert "45%" in drafts[0]["action"]
    assert drafts[1]["has_metric"] is True
    assert "15" in drafts[1]["action"]
    assert drafts[2]["has_metric"] is False

    for d in drafts:
        # Unstated Task is NEVER fabricated
        assert d["task"] == TODO_PLACEHOLDER
        assert TODO_PLACEHOLDER in d["result"]
        # Verify real profile facts appear without invented persona phrases
        assert "delve" not in (d["situation"] + d["action"]).lower()


def test_story_bank_crud_and_coverage(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREERFORGE_DATA_DIR", str(tmp_path))
    bank = StoryBank()
    assert bank.path == os.path.join(str(tmp_path), "stories.yaml")

    s1 = bank.add_story(
        title="SQL pipeline speedup",
        situation="Data Analyst at Northwind Logistics (2023)",
        action="Rewrote correlated subqueries into window functions.",
        tags="ownership, technical_challenge",
    )
    assert s1["id"] == 1
    assert s1["task"] == TODO_PLACEHOLDER
    assert s1["result"] == TODO_PLACEHOLDER
    assert s1["tags"] == ["ownership", "technical_challenge"]

    s2 = bank.add_story(
        title="Missed sprint estimate",
        situation="FreightDelay v1 launch",
        task="Ship milestone by Friday",
        action="Split scope and flagged delay on Wednesday.",
        result="Shipped core parser Friday, UI Monday.",
        tags=["failure", "deadline"],
    )
    assert s2["id"] == 2

    edited = bank.edit_story(1, result="Cut query runtime by 45%.")
    assert edited["result"] == "Cut query runtime by 45%."

    with pytest.raises(InterviewError):
        bank.edit_story(999, title="Missing")

    assert len(bank.list_stories()) == 2
    assert len(bank.list_stories(tag="failure")) == 1

    cov = bank.coverage_report()
    assert cov["total_stories"] == 2
    assert set(cov["covered_categories"]) == {"ownership", "technical_challenge", "failure", "deadline"}
    expected_missing = set(STAR_CATEGORIES) - {"ownership", "technical_challenge", "failure", "deadline"}
    assert set(cov["uncovered_categories"]) == expected_missing


def test_question_banks_and_seeded_practice():
    for role in VALID_ROLES:
        bank = load_questions(role)
        assert len(bank["questions"]) >= 8
        cats = {q["category"] for q in bank["questions"]}
        assert cats == set(STAR_CATEGORIES)

    run1 = select_practice_questions(role="data", seed=42, count=2)
    run2 = select_practice_questions(role="data", seed=42, count=2)
    assert [q["id"] for q in run1["questions"]] == [q["id"] for q in run2["questions"]]


def test_cli_interview_missing_profile_exits_cleanly(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["forge", "interview", "draft"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "forge init" in err


def test_cli_interview_end_to_end_and_audit(tmp_path, monkeypatch, capsys):
    stories_path = str(tmp_path / "stories.yaml")
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    example_profile = os.path.join(repo_root, "examples", "profile.example.yaml")

    # Draft + save JSON
    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "interview", "draft", "--profile", example_profile, "--stories", stories_path, "--limit", "2", "--save", "--json"],
    )
    cli.main()
    draft_out = json.loads(capsys.readouterr().out)
    assert draft_out["draft_count"] == 2
    assert draft_out["saved"]["added_count"] == 2

    # Coverage JSON
    monkeypatch.setattr(
        sys,
        "argv",
        ["forge", "interview", "coverage", "--stories", stories_path, "--json"],
    )
    cli.main()
    cov_out = json.loads(capsys.readouterr().out)
    assert cov_out["total_stories"] == 2
    assert len(cov_out["uncovered_categories"]) == len(STAR_CATEGORIES)

    # Clean practice answer passes --audit
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "forge",
            "interview",
            "practice",
            "--role",
            "data",
            "--seed",
            "7",
            "--timer",
            "90",
            "--answer",
            "Queries timed out at 5 PM. I indexed customer_id and split the batch job. Runtime fell from 40s to 3s.",
            "--audit",
            "--json",
        ],
    )
    cli.main()
    prac_ok = json.loads(capsys.readouterr().out)
    assert prac_ok["timer_seconds"] == 90
    assert prac_ok["audit"]["compliant"] is True

    # Buzzword-laden answer fails --audit with exit code 1
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "forge",
            "interview",
            "practice",
            "--role",
            "general",
            "--seed",
            "7",
            "--answer",
            "Furthermore, we meticulously delved into a dynamic tapestry of synergistic paradigms to bolster outcomes.",
            "--audit",
            "--json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    prac_bad = json.loads(capsys.readouterr().out)
    assert prac_bad["audit"]["compliant"] is False
