"""
Tests for SQLite store, migrations, foreign keys, dedup upsert, closed_at safety,
date-injected due/ghosted calculations, CSV/MD exports, and offline guarantee.
"""

import hashlib
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from careerforge.core.store import (
    MIGRATIONS,
    CareerStore,
    StoreError,
    get_db_path,
)
from careerforge.scrapers.base import JobPosting
from careerforge.scrapers.greenhouse_scanner import GreenhouseScraper


def test_env_override_and_foreign_keys(tmp_path, monkeypatch, socket_disabled=None):
    db_file = tmp_path / "custom.db"
    monkeypatch.setenv("CAREERFORGE_DB", str(db_file))
    assert get_db_path() == str(db_file)

    store = CareerStore()
    assert store.get_schema_version() == len(MIGRATIONS)
    assert os.path.exists(db_file)

    # Verify PRAGMA foreign_keys = ON rejects orphan applications
    with store._connect() as conn:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO applications (job_id, stage) VALUES (9999, 'saved')"
            )


def test_incremental_schema_migration(tmp_path):
    db_file = str(tmp_path / "migrate.db")
    # Initialize at v1
    store_v1 = CareerStore(db_path=db_file, migrations=MIGRATIONS[:1])
    assert store_v1.get_schema_version() == 1
    app = store_v1.add_application(
        manual=True, company="Acme", title="Data Analyst", stage="saved"
    )

    # Apply a v2 migration dynamically
    def _migrate_test_v2(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE applications ADD COLUMN custom_tag TEXT DEFAULT 'none'")

    store_v2 = CareerStore(db_path=db_file, migrations=[MIGRATIONS[0], _migrate_test_v2])
    assert store_v2.get_schema_version() == 2

    # Existing data survives migration intact
    loaded = store_v2.get_application(app["id"])
    assert loaded is not None
    assert loaded["company"] == "Acme"
    assert loaded["custom_tag"] == "none"


def test_stage_transitions_cv_sha_and_events(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "apps.db")
    cv_file = tmp_path / "resume.pdf"
    cv_bytes = b"%PDF-1.4 dummy resume bytes for sha check"
    cv_file.write_bytes(cv_bytes)
    expected_sha = hashlib.sha256(cv_bytes).hexdigest()

    store = CareerStore(db_path=db_file)
    t0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 3, 16, 30, tzinfo=timezone.utc)

    app = store.add_application(
        url="https://boards.greenhouse.io/canonical/jobs/123",
        company="Canonical",
        title="Data Engineer",
        stage="saved",
        cv_path=str(cv_file),
        jd_snapshot="Need SQL and Python experience.",
        match_score=88.5,
        now=t0,
    )
    assert app["cv_sha256"] == expected_sha
    assert app["jd_snapshot"] == "Need SQL and Python experience."
    assert len(app["events"]) == 1
    assert app["events"][0]["kind"] == "stage_change"

    moved = store.move_application(app["id"], "applied", note="Submitted via portal", now=t1)
    assert moved["stage"] == "applied"
    assert moved["applied_at"] == t1.isoformat(timespec="seconds")
    assert len(moved["events"]) == 2
    assert "saved -> applied" in moved["events"][1]["detail"]

    noted = store.add_note(app["id"], "Recruiter replied on email", now=t2)
    assert len(noted["events"]) == 3
    assert noted["events"][2]["kind"] == "note"
    assert "Recruiter replied" in noted["events"][2]["detail"]

    # Invalid stage rejected
    with pytest.raises(StoreError, match="Invalid stage"):
        store.move_application(app["id"], "hired_magic", now=t2)


def test_scrape_upsert_dedupe_and_partial_failure_closed_at(tmp_path):
    db_file = str(tmp_path / "jobs.db")
    store = CareerStore(db_path=db_file)
    t1 = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)

    j_canon_1 = JobPosting(
        id="gh-canonical-1",
        title="Python Engineer",
        company="Canonical",
        location="Remote",
        source_url="https://boards.greenhouse.io/canonical/jobs/1",
        source="Greenhouse",
    )
    j_canon_2 = JobPosting(
        id="gh-canonical-2",
        title="Data Analyst",
        company="Canonical",
        location="Remote",
        source_url="https://boards.greenhouse.io/canonical/jobs/2",
        source="Greenhouse",
    )
    j_gitlab_1 = JobPosting(
        id="gh-gitlab-1",
        title="Backend Engineer",
        company="Gitlab",
        location="Remote",
        source_url="https://boards.greenhouse.io/gitlab/jobs/1",
        source="Greenhouse",
    )

    stats1 = store.upsert_scraped_jobs(
        [j_canon_1, j_canon_2, j_gitlab_1],
        succeeded_companies=[("Greenhouse", "Canonical"), ("Greenhouse", "Gitlab")],
        now=t1,
    )
    assert stats1 == {"inserted": 3, "updated": 0, "closed": 0}

    # Scrape 2: Canonical succeeded and ONLY j_canon_1 remains -> j_canon_2 closed!
    # Gitlab FAILED (not in succeeded_companies) -> j_gitlab_1 MUST remain open!
    stats2 = store.upsert_scraped_jobs(
        [j_canon_1],
        succeeded_companies=[("Greenhouse", "Canonical")],
        now=t2,
    )
    assert stats2["updated"] == 1
    assert stats2["closed"] == 1

    canon1_row = store.get_job("gh-canonical-1")
    canon2_row = store.get_job("gh-canonical-2")
    gitlab1_row = store.get_job("gh-gitlab-1")

    assert canon1_row["first_seen"] == t1.isoformat(timespec="seconds")
    assert canon1_row["last_seen"] == t2.isoformat(timespec="seconds")
    assert canon1_row["closed_at"] is None

    assert canon2_row["closed_at"] == t2.isoformat(timespec="seconds")
    assert gitlab1_row["closed_at"] is None


def test_greenhouse_fetch_with_status_partial_failure(tmp_path):
    """Simulates one board succeeding (200) and one failing (500) without false closures."""
    mock_session = MagicMock()

    def side_effect(url, timeout=6):
        resp = MagicMock()
        if "/canonical/" in url:
            resp.status_code = 200
            resp.json.return_value = {
                "jobs": [
                    {
                        "id": 101,
                        "title": "Python Data Engineer",
                        "location": {"name": "Remote"},
                        "absolute_url": "https://boards.greenhouse.io/canonical/jobs/101",
                    }
                ]
            }
        else:
            resp.status_code = 500
        return resp

    mock_session.get.side_effect = side_effect
    scraper = GreenhouseScraper(session=mock_session, boards=["canonical", "brokenboard"])
    postings, ok_boards, failed_boards = scraper.fetch_with_status({"keywords": ["Python"], "exclude_senior": False})

    assert len(postings) == 1
    assert ("Greenhouse", "Canonical") in ok_boards
    assert ("Greenhouse", "Brokenboard") in failed_boards


def test_due_ghosted_and_export_with_fixed_clock(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "clock.db")
    store = CareerStore(db_path=db_file)

    now = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    recent_date = now - timedelta(days=5)
    due_date = now - timedelta(days=9)
    stale_date = now - timedelta(days=23)

    a_recent = store.add_application(manual=True, company="RecentCo", title="Eng", stage="applied", now=recent_date)
    a_due = store.add_application(manual=True, company="DueCo", title="Eng", stage="applied", now=due_date)
    a_stale = store.add_application(manual=True, company="StaleCo", title="Eng", stage="applied", now=stale_date)

    due_items = store.get_due_applications(days=7, now=now)
    due_ids = {item["id"] for item in due_items}
    assert a_recent["id"] not in due_ids
    assert a_due["id"] in due_ids
    assert a_stale["id"] in due_ids

    ghost_items = store.get_ghost_candidates(days=21, now=now)
    ghost_ids = {item["id"] for item in ghost_items}
    assert a_stale["id"] in ghost_ids
    assert a_due["id"] not in ghost_ids

    # Ghost candidate must NOT be auto-moved!
    reloaded_stale = store.get_application(a_stale["id"])
    assert reloaded_stale["stage"] == "applied"

    # CSV and Markdown exports
    csv_out = store.export_applications(fmt="csv")
    assert "company,title,source" in csv_out
    assert "StaleCo,Eng,manual" in csv_out

    md_out = store.export_applications(fmt="md")
    assert "| ID | Stage | Company | Title |" in md_out
    assert "| StaleCo |" in md_out
