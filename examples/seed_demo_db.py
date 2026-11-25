"""
Offline Demo Database Seeder for CareerForge (Alex Rivera persona).
Populates an isolated SQLite database with 100% fictional postings and tracked
applications across stages so 'track', 'report', 'ghost', 'salary', and
'cover --type follow-up --app' can be explored cleanly without live scrapes.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from datetime import datetime, timedelta, timezone

from careerforge.core.store import CareerStore
from careerforge.scrapers.base import JobPosting


def seed_demo_db(db_path: str) -> dict:
    if os.path.exists(db_path):
        os.remove(db_path)

    store = CareerStore(db_path=db_path)
    now = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)

    postings = [
        (
            JobPosting(
                id="demo-gh-101",
                source="greenhouse",
                source_url="https://boards.greenhouse.io/northwinddata/jobs/101",
                title="Data & Analytics Engineer",
                company="Northwind Data Systems",
                location="Remote - Worldwide",
                salary_min=95000.0,
                salary_max=115000.0,
                salary_currency="USD",
                description=(
                    "Responsibilities: Build SQL pipelines, FastAPI endpoints, and PostgreSQL marts. "
                    "Requirements: Python, SQL, Docker, REST API experience."
                ),
                posted_at=(now - timedelta(days=5)).isoformat(),
            ),
            now - timedelta(days=5),
        ),
        (
            JobPosting(
                id="demo-lever-202",
                source="lever",
                source_url="https://jobs.lever.co/harborfreight/202",
                title="Senior Backend Platform Engineer",
                company="Harbor Freight Tech",
                location="Remote - US Only",
                salary_min=135000.0,
                salary_max=160000.0,
                salary_currency="USD",
                description=(
                    "Candidates must reside in the US and be authorized to work without visa sponsorship. "
                    "Requirements: FastAPI, Kubernetes, PostgreSQL, Redis."
                ),
                posted_at=(now - timedelta(days=68)).isoformat(),
            ),
            now - timedelta(days=68),
        ),
        (
            JobPosting(
                id="demo-ashby-303",
                source="ashby",
                source_url="https://jobs.ashbyhq.com/beaconhealth/303",
                title="Analytics Engineer",
                company="Beacon Health Labs",
                location="Remote",
                salary_min=105000.0,
                salary_max=125000.0,
                salary_currency="USD",
                description="Requirements: Python, PostgreSQL, schema design, automated testing.",
                posted_at=(now - timedelta(days=12)).isoformat(),
            ),
            now - timedelta(days=12),
        ),
        (
            JobPosting(
                id="demo-rem-404",
                source="remotive",
                source_url="https://remotive.com/remote-jobs/404",
                title="Python Backend Developer",
                company="Summit FinOps",
                location="Worldwide",
                salary_min=85000.0,
                salary_max=100000.0,
                salary_currency="EUR",
                description="Looking for Django/FastAPI and SQL engineers.",
                posted_at=(now - timedelta(days=45)).isoformat(),
            ),
            now - timedelta(days=45),
        ),
        (
            JobPosting(
                id="demo-gh-505",
                source="greenhouse",
                source_url="https://boards.greenhouse.io/cascadelogistics/jobs/505",
                title="Platform Data Engineer",
                company="Cascade Logistics",
                location="Remote",
                salary_min=110000.0,
                salary_max=130000.0,
                salary_currency="USD",
                description="General pipeline pool.",
                posted_at=(now - timedelta(days=75)).isoformat(),
            ),
            now - timedelta(days=75),
        ),
    ]

    for posting, seen_at in postings:
        store.upsert_scraped_jobs([posting], succeeded_companies=[], now=seen_at)

    # Refresh an older evergreen posting so unchanged hash triggers heuristic signal
    store.upsert_scraped_jobs([postings[1][0]], succeeded_companies=[], now=now - timedelta(days=2))

    hash_a = hashlib.sha256(b"alex_rivera_tailored_v1").hexdigest()
    hash_b = hashlib.sha256(b"alex_rivera_universal_v2").hexdigest()

    app1 = store.add_application(
        job_id="demo-gh-101",
        stage="applied",
        jd_snapshot=postings[0][0].description,
        match_score=86.0,
        notes="Submitted tailored FastAPI + SQL CV",
        now=now - timedelta(days=10),
    )
    with store._connect() as conn:
        conn.execute("UPDATE applications SET cv_sha256 = ? WHERE id = ?", (hash_a, app1["id"]))
        conn.commit()

    app2 = store.add_application(
        job_id="demo-ashby-303",
        stage="screen",
        jd_snapshot=postings[2][0].description,
        match_score=91.5,
        notes="Recruiter intro completed",
        now=now - timedelta(days=14),
    )
    with store._connect() as conn:
        conn.execute(
            "UPDATE applications SET applied_at = ?, cv_sha256 = ? WHERE id = ?",
            ((now - timedelta(days=14)).isoformat(timespec="seconds"), hash_a, app2["id"]),
        )
        conn.commit()
    store.move_application(app2["id"], "interview", note="Technical SQL screen scheduled", now=now - timedelta(days=3))

    app3 = store.add_application(
        url="https://jobs.ashbyhq.com/example/606",
        company="Riverbank Analytics",
        title="Backend Systems Engineer",
        stage="rejected",
        jd_snapshot="Need Go and Kubernetes",
        match_score=64.0,
        now=now - timedelta(days=28),
    )
    with store._connect() as conn:
        conn.execute(
            "UPDATE applications SET applied_at = ?, cv_sha256 = ? WHERE id = ?",
            ((now - timedelta(days=28)).isoformat(timespec="seconds"), hash_b, app3["id"]),
        )
        conn.commit()

    return {
        "db_path": db_path,
        "jobs_seeded": len(postings),
        "applications_seeded": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed isolated CareerForge demo SQLite DB")
    parser.add_argument("--db", required=True, help="Output SQLite file path")
    args = parser.parse_args()
    summary = seed_demo_db(args.db)
    print(f"Seeded {summary['jobs_seeded']} jobs and {summary['applications_seeded']} applications into {summary['db_path']}")


if __name__ == "__main__":
    main()
