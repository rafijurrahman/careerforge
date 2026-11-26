"""Tests for grouped CLI help output, demo DB seeder, and sanitized sample fixtures."""

from __future__ import annotations

import json
import os
import sys

import pytest

from careerforge import __version__, cli
from careerforge.core.store import CareerStore


def test_version_is_0_5_1():
    assert __version__ == "0.5.1"


def test_grouped_cli_help_renders_all_workflow_sections(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "--help"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0

    help_out = capsys.readouterr().out
    for group in ("Find:", "Match:", "Build:", "Track:", "Prepare:", "Setup & Diagnostics:"):
        assert group in help_out

    for cmd in (
        "scrape",
        "dorks",
        "match",
        "eligibility",
        "tailor",
        "apply",
        "ats-sim",
        "audit",
        "track",
        "report",
        "ghost",
        "salary",
        "interview",
        "cover",
        "init",
        "setup",
        "doctor",
    ):
        assert cmd in help_out


def test_seed_demo_db_and_sanitized_sample_outputs(tmp_path):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from examples.seed_demo_db import seed_demo_db

    demo_db = str(tmp_path / "demo.db")
    summary = seed_demo_db(demo_db)
    assert summary["jobs_seeded"] == 5
    assert summary["applications_seeded"] == 3

    store = CareerStore(db_path=demo_db)
    assert len(store.list_applications()) == 3

    sample_dir = os.path.join(repo_root, "examples", "sample_output")
    expected_json = (
        "ats_sim_sample.json",
        "track_list_sample.json",
        "report_sample.json",
        "ghost_sample.json",
        "salary_sample.json",
        "eligibility_sample.json",
        "interview_draft_sample.json",
        "cover_sample.json",
    )
    forbidden = ("rafizurrahman3", "zuboraj", "c:\\users", "c:/users")
    for fname in expected_json:
        fpath = os.path.join(sample_dir, fname)
        assert os.path.exists(fpath), f"Missing sample output: {fname}"
        with open(fpath, "r", encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
        assert data is not None
        low = raw.lower()
        for bad in forbidden:
            assert bad not in low, f"Forbidden string '{bad}' leaked in {fname}"
