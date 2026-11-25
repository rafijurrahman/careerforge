"""
Tests for `forge report`, `forge ghost`, and `forge salary`, plus schema v2 migration.
Verifies exact conversion %, Ghost Risk scoring, percentile calculations,
small-sample / selection-bias warnings, and zero network connections.
"""

import json
import sys
from datetime import datetime, timedelta, timezone

import pytest

from careerforge.cli import main
from careerforge.core.ghost import GHOST_NOTICE, analyze_ghost_jobs
from careerforge.core.reporter import ReportError, generate_report
from careerforge.core.salary import SELECTION_BIAS_WARNING, SalaryError, analyze_salaries
from careerforge.core.store import MIGRATIONS, CareerStore
from careerforge.scrapers.base import JobPosting


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


def test_v1_to_v2_migration_backfills_description_hash(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "upgrade_v2.db")
    # Build v1 store first and insert a job using v1 columns (simulating pre-v2 data)
    s1 = CareerStore(db_path=db_file, migrations=MIGRATIONS[:1])
    with s1._connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (dedupe_hash, source, external_id, company, title, location, description, first_seen, last_seen)
            VALUES ('hashv1', 'Greenhouse', 'gh-1', 'Acme', 'Data Analyst', 'Remote',
                    'Analyze SQL tables and build Power BI dashboards cleanly.',
                    '2026-11-01T10:00:00+00:00', '2026-11-01T10:00:00+00:00')
            """
        )
    assert s1.get_schema_version() == 1

    # Opening full store triggers v2 migration and backfills description_hash
    s2 = CareerStore(db_path=db_file)
    assert s2.get_schema_version() == 2
    job = s2.get_job("gh-1")
    assert job is not None
    assert len(job["description_hash"]) == 16
    assert job["description_changed_at"] == "2026-11-01T10:00:00+00:00"


def test_report_funnel_cv_breakdown_and_small_sample(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "report.db")
    store = CareerStore(db_path=db_file)

    cv_a = tmp_path / "cv_a.pdf"
    cv_a.write_bytes(b"resume version A")
    cv_b = tmp_path / "cv_b.pdf"
    cv_b.write_bytes(b"resume version B")

    t0 = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    t_screen = datetime(2026, 11, 5, 10, 0, tzinfo=timezone.utc)  # 4 days after apply
    t_int = datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc)
    t_now = datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc)

    # App 1: saved -> applied -> screen -> interview -> offer (CV A, Greenhouse)
    a1 = store.add_application(
        url="https://boards.greenhouse.io/a/jobs/1",
        company="CoA",
        title="Backend Eng",
        stage="applied",
        cv_path=str(cv_a),
        now=t0,
    )
    store.move_application(a1["id"], "screen", now=t_screen)
    store.move_application(a1["id"], "interview", now=t_int)
    store.move_application(a1["id"], "offer", now=t_int + timedelta(days=3))

    # App 2: applied -> rejected (CV A, Ashby)
    a2 = store.add_application(
        manual=True,
        company="CoB",
        title="Backend Eng",
        stage="applied",
        cv_path=str(cv_a),
        now=t0,
    )
    store.move_application(a2["id"], "rejected", now=t_screen)

    # App 3: saved only (CV B)
    store.add_application(
        manual=True,
        company="CoC",
        title="Data Analyst",
        stage="saved",
        cv_path=str(cv_b),
        now=t0,
    )

    rep = generate_report(store, now=t_now)
    assert rep["total_applications"] == 3
    assert rep["total_applied"] == 2
    assert rep["sample_too_small"] is True
    assert any("Sample too small" in w for w in rep["warnings"])
    assert rep["avg_response_days"] == 4.0

    funnel = {step["stage"]: step for step in rep["funnel"]}
    assert funnel["saved"]["count"] == 3
    assert funnel["applied"]["count"] == 2
    assert funnel["screen"]["count"] == 1
    assert funnel["interview"]["count"] == 1
    assert funnel["offer"]["count"] == 1
    assert funnel["screen"]["step_conversion_pct"] == 50.0
    assert len(rep["funnel_sparkline"]) == 5

    # Invalid --since must raise ReportError
    with pytest.raises(ReportError):
        generate_report(store, since="not-a-date", now=t_now)


def test_ghost_risk_scoring_levels_and_reposts(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "ghost.db")
    store = CareerStore(db_path=db_file)

    now = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)
    old_date = now - timedelta(days=70)
    mid_date = now - timedelta(days=35)

    # High risk job: posted 70d ago (+25), reposted twice across locations (+15),
    # vague short JD with no salary (+15), unchanged desc hash >= 30d (+15) -> High (>=60)
    store.upsert_scraped_jobs(
        [
            JobPosting(
                id="ghost-1",
                title="Data Engineer",
                company="PhantomCorp",
                location="Remote - US",
                description="Apply quickly.",
                posted_at=old_date.isoformat(timespec="seconds"),
                source_url="https://example.com/p1",
                source="Greenhouse",
            ),
            JobPosting(
                id="ghost-1-dup",
                title="Data Engineer",
                company="PhantomCorp",
                location="Remote - EU",
                description="Apply quickly.",
                posted_at=mid_date.isoformat(timespec="seconds"),
                source_url="https://example.com/p2",
                source="Greenhouse",
            ),
        ],
        now=old_date,
    )
    # Re-scrape 40 days later keeping identical description_hash while last_seen updates
    store.upsert_scraped_jobs(
        [
            JobPosting(
                id="ghost-1",
                title="Data Engineer",
                company="PhantomCorp",
                location="Remote - US",
                description="Apply quickly.",
                source_url="https://example.com/p1",
                source="Greenhouse",
            )
        ],
        now=now,
    )

    # Low risk fresh job with disclosed salary & concrete responsibilities
    store.upsert_scraped_jobs(
        [
            JobPosting(
                id="clean-1",
                title="Python Backend Engineer",
                company="SolidLabs",
                location="Remote",
                salary_min=130000,
                salary_max=150000,
                currency="USD",
                description=(
                    "Responsibilities: Build PostgreSQL data APIs, optimize Redis latency, "
                    "and write automated tests. Requirements: 3+ years Python experience."
                ),
                posted_at=(now - timedelta(days=3)).isoformat(timespec="seconds"),
                source_url="https://example.com/solid",
                source="Ashby",
            )
        ],
        now=now - timedelta(days=3),
    )

    res = analyze_ghost_jobs(store, top=10, now=now)
    assert res["heuristic"] is True
    assert GHOST_NOTICE in res["notice"]

    by_title = {item["title"]: item for item in res["items"]}
    # ghost-1 has age>=60 (+25), repost_count=2 (+15), vague JD (+15), unchanged hash (+15) = 70 -> High
    high_item = next(i for i in res["items"] if i["company"] == "PhantomCorp" and i["age_days"] >= 60)
    assert high_item["risk_level"] == "High"
    assert high_item["repost_count"] == 2
    assert high_item["risk_score"] >= 60

    low_item = by_title["Python Backend Engineer"]
    assert low_item["risk_level"] == "Low"
    assert low_item["risk_score"] < 30


def test_salary_percentiles_user_rates_and_warnings(tmp_path, socket_disabled=None):
    db_file = str(tmp_path / "salary.db")
    store = CareerStore(db_path=db_file)

    store.upsert_scraped_jobs(
        [
            JobPosting(
                id="sal-1",
                title="Data Analyst",
                company="Co1",
                salary_min=80000,
                salary_max=100000,  # mid = 90k USD
                currency="USD",
                source_url="https://example.com/1",
                source="Greenhouse",
            ),
            JobPosting(
                id="sal-2",
                title="Senior Data Analyst",
                company="Co2",
                salary_min=110000,
                salary_max=130000,  # mid = 120k USD
                currency="USD",
                source_url="https://example.com/2",
                source="Greenhouse",
            ),
            JobPosting(
                id="sal-3",
                title="Data Analyst",
                company="Co3",
                salary_min=100000,
                salary_max=100000,  # 100k EUR -> with 1.1 rate = 110k USD
                currency="EUR",
                source_url="https://example.com/3",
                source="Ashby",
            ),
            JobPosting(
                id="sal-none",
                title="Data Analyst",
                company="Co4",
                source_url="https://example.com/4",
                source="Ashby",
            ),
        ]
    )

    # Without rates: separates USD (2) and EUR (1)
    res_raw = analyze_salaries(store, role="Data Analyst")
    assert res_raw["heuristic"] is True
    assert res_raw["sample_too_small"] is True
    assert SELECTION_BIAS_WARNING in res_raw["warnings"]
    assert any("Sample too small" in w for w in res_raw["warnings"])

    usd_bucket = next(b for b in res_raw["buckets"] if b["currency"] == "USD")
    assert usd_bucket["count"] == 2
    assert usd_bucket["median"] == 105000.0
    assert usd_bucket["min"] == 80000.0
    assert usd_bucket["max"] == 130000.0

    # With user-supplied rates YAML
    rates_file = tmp_path / "rates.yaml"
    rates_file.write_text("base: USD\nrates:\n  USD: 1.0\n  EUR: 1.1\n", encoding="utf-8")

    res_conv = analyze_salaries(store, role="Data Analyst", rates_path=str(rates_file))
    assert len(res_conv["buckets"]) == 1
    b_usd = res_conv["buckets"][0]
    assert b_usd["currency"] == "USD"
    assert b_usd["count"] == 3
    # Sorted midpoints: [90000, 110000, 120000] -> median == 110000
    assert b_usd["median"] == 110000.0

    # Invalid rates path
    with pytest.raises(SalaryError):
        analyze_salaries(store, rates_path=str(tmp_path / "missing_rates.yaml"))


def test_cli_report_ghost_salary_json_and_errors(tmp_path, monkeypatch, capsys, socket_disabled=None):
    db_file = str(tmp_path / "cli_rgs.db")
    monkeypatch.setenv("CAREERFORGE_DB", db_file)

    store = CareerStore(db_path=db_file)
    store.upsert_scraped_jobs(
        [
            JobPosting(
                id="cli-j1",
                title="Backend Engineer",
                company="DemoCo",
                salary_min=100000,
                salary_max=120000,
                currency="USD",
                source_url="https://example.com/j1",
                source="Greenhouse",
            )
        ]
    )
    store.add_application(job_id="cli-j1", stage="applied")

    # report --json
    assert _run_cli(["report", "--json"], monkeypatch) == 0
    rep_json = json.loads(capsys.readouterr().out)
    assert rep_json["total_applied"] == 1

    # ghost --json
    assert _run_cli(["ghost", "--top", "5", "--json"], monkeypatch) == 0
    ghost_json = json.loads(capsys.readouterr().out)
    assert ghost_json["heuristic"] is True
    assert ghost_json["count"] == 1

    # ghost invalid job -> exit 2
    assert _run_cli(["ghost", "nonexistent-id"], monkeypatch) == 2
    capsys.readouterr()

    # salary --json
    assert _run_cli(["salary", "--role", "Backend", "--json"], monkeypatch) == 0
    sal_json = json.loads(capsys.readouterr().out)
    assert sal_json["total_disclosed"] == 1

    # report invalid --since -> exit 2
    assert _run_cli(["report", "--since", "bad-date"], monkeypatch) == 2
    assert "Invalid --since" in capsys.readouterr().err
