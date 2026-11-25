"""
Offline SQLite Persistence Layer for CareerForge.
Uses stdlib sqlite3 (no ORM) with platformdirs paths, CAREERFORGE_DB override,
PRAGMA foreign_keys=ON, and PRAGMA user_version schema migrations.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

import platformdirs

try:
    from careerforge.scrapers.base import JobPosting, compute_dedup_hash
except ImportError:
    from scrapers.base import JobPosting, compute_dedup_hash

VALID_STAGES: Tuple[str, ...] = (
    "saved",
    "applied",
    "screen",
    "interview",
    "offer",
    "rejected",
    "ghosted",
)

ACTIVE_STAGES: Tuple[str, ...] = ("applied", "screen", "interview")


class StoreError(Exception):
    """Base exception for CareerForge store operations."""


def get_db_path(explicit_path: Optional[str] = None) -> str:
    """
    Resolves SQLite database path:
    1. Explicit path argument if given
    2. CAREERFORGE_DB environment variable if set
    3. platformdirs user data directory ('careerforge.db')
    """
    if explicit_path:
        path = explicit_path
    elif os.environ.get("CAREERFORGE_DB"):
        path = os.environ["CAREERFORGE_DB"]
    else:
        data_dir = platformdirs.user_data_dir("careerforge", appauthor=False)
        path = os.path.join(data_dir, "careerforge.db")

    if path != ":memory:":
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
    return path


def utc_now_iso(now: Optional[datetime] = None) -> str:
    """Formats a datetime as UTC ISO-8601 string compatible with Python 3.10+."""
    if now is None:
        dt = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        dt = now.replace(tzinfo=timezone.utc)
    else:
        dt = now.astimezone(timezone.utc)
    return dt.isoformat(timespec="seconds")


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parses an ISO-8601 timestamp safely across Python 3.10+."""
    if not ts:
        return None
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 hex digest of a file."""
    if not os.path.exists(file_path):
        raise StoreError(f"CV file not found: '{file_path}'")
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _migrate_v1(conn: sqlite3.Connection) -> None:
    """Initial v1 schema: jobs, applications, events."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dedupe_hash TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            external_id TEXT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT DEFAULT '',
            remote_policy TEXT DEFAULT '',
            salary_min REAL,
            salary_max REAL,
            currency TEXT,
            url TEXT DEFAULT '',
            description TEXT DEFAULT '',
            posted_at TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            closed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER UNIQUE NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            stage TEXT NOT NULL CHECK (stage IN ('saved','applied','screen','interview','offer','rejected','ghosted')),
            applied_at TEXT,
            next_action_at TEXT,
            cv_path TEXT,
            cv_sha256 TEXT,
            jd_snapshot TEXT DEFAULT '',
            match_score REAL,
            notes TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            at TEXT NOT NULL,
            kind TEXT NOT NULL,
            detail TEXT DEFAULT ''
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_source_company ON jobs(source, company);
        CREATE INDEX IF NOT EXISTS idx_apps_stage ON applications(stage);
        CREATE INDEX IF NOT EXISTS idx_events_app_id ON events(application_id);
        """
    )


MIGRATIONS: List[Callable[[sqlite3.Connection], None]] = [
    _migrate_v1,
]


def _infer_company_from_url(url: str) -> str:
    """Best-effort company inference from ATS URLs when company not specified."""
    try:
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        host = parsed.netloc.lower()
        if "greenhouse.io" in host and parts:
            return parts[0].capitalize()
        if "ashbyhq.com" in host and parts:
            return parts[0].capitalize()
        if "lever.co" in host and parts:
            return parts[0].capitalize()
        if host:
            return host.replace("www.", "").split(".")[0].capitalize()
    except Exception:
        pass
    return "Unknown"


class CareerStore:
    """SQLite database store for jobs, applications, and timeline events."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        migrations: Optional[Sequence[Callable[[sqlite3.Connection], None]]] = None,
    ):
        self.db_path = get_db_path(db_path)
        self._migrations = list(migrations) if migrations is not None else list(MIGRATIONS)
        self._apply_migrations()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _apply_migrations(self) -> None:
        with self._connect() as conn:
            current_ver = int(conn.execute("PRAGMA user_version").fetchone()[0])
            for target_ver, migrate_fn in enumerate(self._migrations, start=1):
                if current_ver < target_ver:
                    migrate_fn(conn)
                    conn.execute(f"PRAGMA user_version = {target_ver}")
                    current_ver = target_ver

    def get_schema_version(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("PRAGMA user_version").fetchone()[0])

    # ------------------------------------------------------------------
    # Jobs & Scraping Upsert
    # ------------------------------------------------------------------

    def upsert_scraped_jobs(
        self,
        postings: Iterable[Any],
        succeeded_boards: Optional[Dict[Tuple[str, str], Set[str]]] = None,
        succeeded_companies: Optional[Iterable[Tuple[str, str]]] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Upserts scraped job postings into `jobs` using `dedupe_hash`.

        - New job: sets `first_seen = now`, `last_seen = now`.
        - Existing job: updates `last_seen = now`, resets `closed_at = NULL`, refreshes mutable fields.
        - Closed detection: ONLY for (source, company) pairs that succeeded cleanly
          (either in `succeeded_boards` or `succeeded_companies`), marks previously open jobs
          that did not appear in the live board result with `closed_at = now`.
        """
        now_iso = utc_now_iso(now)
        inserted = 0
        updated = 0
        closed = 0

        postings_list = list(postings)
        seen_per_board: Dict[Tuple[str, str], Set[str]] = {}

        if succeeded_boards:
            for key, seen_ids in succeeded_boards.items():
                norm_key = (key[0].strip().lower(), key[1].strip().lower())
                seen_per_board[norm_key] = set(seen_ids)

        if succeeded_companies:
            for src, comp in succeeded_companies:
                norm_key = (src.strip().lower(), comp.strip().lower())
                seen_per_board.setdefault(norm_key, set())

        with self._connect() as conn:
            for item in postings_list:
                if isinstance(item, JobPosting):
                    ext_id = item.id
                    title = item.title
                    company = item.company
                    location = item.location or ""
                    remote_policy = item.remote_policy or ""
                    salary_min = item.salary_min
                    salary_max = item.salary_max
                    currency = item.currency
                    url = item.source_url
                    description = item.description or ""
                    posted_at = item.posted_at
                    source = item.source
                else:
                    ext_id = item.get("id") or item.get("external_id")
                    title = item.get("title", "")
                    company = item.get("company", "Unknown")
                    location = item.get("location", "") or ""
                    remote_policy = item.get("remote_policy", "") or ""
                    salary_min = item.get("salary_min")
                    salary_max = item.get("salary_max")
                    currency = item.get("currency")
                    url = item.get("url") or item.get("source_url") or ""
                    description = item.get("description") or ""
                    posted_at = item.get("posted_at") or item.get("published_at")
                    source = item.get("source") or item.get("platform") or "Manual"

                d_hash = compute_dedup_hash(company, title, location)
                board_key = (source.strip().lower(), company.strip().lower())
                if board_key in seen_per_board:
                    seen_per_board[board_key].add(d_hash)
                    if ext_id:
                        seen_per_board[board_key].add(str(ext_id))

                existing = conn.execute(
                    "SELECT id FROM jobs WHERE dedupe_hash = ?",
                    (d_hash,),
                ).fetchone()

                if existing is None:
                    conn.execute(
                        """
                        INSERT INTO jobs (
                            dedupe_hash, source, external_id, company, title,
                            location, remote_policy, salary_min, salary_max, currency,
                            url, description, posted_at, first_seen, last_seen, closed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                        """,
                        (
                            d_hash,
                            source,
                            ext_id,
                            company,
                            title,
                            location,
                            remote_policy,
                            salary_min,
                            salary_max,
                            currency,
                            url,
                            description,
                            posted_at,
                            now_iso,
                            now_iso,
                        ),
                    )
                    inserted += 1
                else:
                    conn.execute(
                        """
                        UPDATE jobs
                        SET last_seen = ?,
                            closed_at = NULL,
                            external_id = COALESCE(NULLIF(?, ''), external_id),
                            remote_policy = COALESCE(NULLIF(?, ''), remote_policy),
                            salary_min = COALESCE(?, salary_min),
                            salary_max = COALESCE(?, salary_max),
                            currency = COALESCE(?, currency),
                            url = COALESCE(NULLIF(?, ''), url),
                            description = CASE WHEN ? != '' THEN ? ELSE description END,
                            posted_at = COALESCE(?, posted_at)
                        WHERE id = ?
                        """,
                        (
                            now_iso,
                            ext_id,
                            remote_policy,
                            salary_min,
                            salary_max,
                            currency,
                            url,
                            description,
                            description,
                            posted_at,
                            existing["id"],
                        ),
                    )
                    updated += 1

            # Close disappeared jobs ONLY on companies whose boards were cleanly fetched
            for (src_low, comp_low), seen_tokens in seen_per_board.items():
                open_rows = conn.execute(
                    """
                    SELECT id, dedupe_hash, external_id
                    FROM jobs
                    WHERE LOWER(source) = ? AND LOWER(company) = ? AND closed_at IS NULL
                    """,
                    (src_low, comp_low),
                ).fetchall()
                for row in open_rows:
                    still_open = (row["dedupe_hash"] in seen_tokens) or (
                        row["external_id"] and str(row["external_id"]) in seen_tokens
                    )
                    if not still_open:
                        conn.execute(
                            "UPDATE jobs SET closed_at = ? WHERE id = ?",
                            (now_iso, row["id"]),
                        )
                        closed += 1

        return {"inserted": inserted, "updated": updated, "closed": closed}

    def get_job(self, identifier: Any) -> Optional[Dict[str, Any]]:
        """Finds a job by integer ID, external_id, or dedupe_hash prefix."""
        with self._connect() as conn:
            row = None
            try:
                int_id = int(identifier)
                row = conn.execute("SELECT * FROM jobs WHERE id = ?", (int_id,)).fetchone()
            except (ValueError, TypeError):
                pass

            if row is None and identifier is not None:
                ident_str = str(identifier).strip()
                row = conn.execute(
                    "SELECT * FROM jobs WHERE external_id = ? OR dedupe_hash = ?",
                    (ident_str, ident_str),
                ).fetchone()
                if row is None and len(ident_str) >= 4:
                    row = conn.execute(
                        "SELECT * FROM jobs WHERE dedupe_hash LIKE ? LIMIT 1",
                        (f"{ident_str}%",),
                    ).fetchone()
            return dict(row) if row else None

    def list_jobs(self, limit: int = 100, include_closed: bool = True) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if include_closed:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY last_seen DESC, id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE closed_at IS NULL ORDER BY last_seen DESC, id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Applications & Events
    # ------------------------------------------------------------------

    def add_application(
        self,
        job_id: Optional[Any] = None,
        url: Optional[str] = None,
        manual: bool = False,
        company: Optional[str] = None,
        title: Optional[str] = None,
        location: str = "Remote",
        stage: str = "saved",
        cv_path: Optional[str] = None,
        jd_snapshot: Optional[str] = None,
        match_score: Optional[float] = None,
        notes: str = "",
        due_days: int = 7,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Adds an application linked to a job and writes the initial event row."""
        stage_clean = stage.strip().lower()
        if stage_clean not in VALID_STAGES:
            raise StoreError(
                f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"
            )

        now_dt = now or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        now_iso = utc_now_iso(now_dt)

        cv_sha256: Optional[str] = None
        norm_cv_path: Optional[str] = None
        if cv_path:
            cv_sha256 = compute_file_sha256(cv_path)
            norm_cv_path = os.path.abspath(cv_path)

        with self._connect() as conn:
            resolved_job_id: Optional[int] = None
            job_description: str = ""

            if job_id is not None:
                job_row = None
                try:
                    job_row = conn.execute(
                        "SELECT * FROM jobs WHERE id = ?",
                        (int(job_id),),
                    ).fetchone()
                except (ValueError, TypeError):
                    job_row = conn.execute(
                        "SELECT * FROM jobs WHERE external_id = ? OR dedupe_hash = ?",
                        (str(job_id), str(job_id)),
                    ).fetchone()
                if job_row is None:
                    raise StoreError(f"Job not found: '{job_id}'")
                resolved_job_id = job_row["id"]
                job_description = job_row["description"] or ""

            elif url:
                job_row = conn.execute(
                    "SELECT * FROM jobs WHERE url = ?",
                    (url.strip(),),
                ).fetchone()
                if job_row is not None:
                    resolved_job_id = job_row["id"]
                    job_description = job_row["description"] or ""
                else:
                    comp = company or _infer_company_from_url(url)
                    role_title = title or "Untitled Role"
                    d_hash = compute_dedup_hash(comp, role_title, f"{location}:{url.strip()}")
                    existing_hash = conn.execute(
                        "SELECT id, description FROM jobs WHERE dedupe_hash = ?",
                        (d_hash,),
                    ).fetchone()
                    if existing_hash:
                        resolved_job_id = existing_hash["id"]
                        job_description = existing_hash["description"] or ""
                    else:
                        cur = conn.execute(
                            """
                            INSERT INTO jobs (
                                dedupe_hash, source, company, title, location,
                                remote_policy, url, description, first_seen, last_seen
                            ) VALUES (?, 'url', ?, ?, ?, 'Remote', ?, ?, ?, ?)
                            """,
                            (
                                d_hash,
                                comp,
                                role_title,
                                location,
                                url.strip(),
                                jd_snapshot or "",
                                now_iso,
                                now_iso,
                            ),
                        )
                        resolved_job_id = int(cur.lastrowid)
                        job_description = jd_snapshot or ""

            elif manual:
                if not company or not title:
                    raise StoreError("Manual application creation requires --company and --title.")
                d_hash = compute_dedup_hash(company, title, f"{location}:{now_iso}")
                existing_hash = conn.execute(
                    "SELECT id, description FROM jobs WHERE dedupe_hash = ?",
                    (d_hash,),
                ).fetchone()
                if existing_hash:
                    resolved_job_id = existing_hash["id"]
                    job_description = existing_hash["description"] or ""
                else:
                    cur = conn.execute(
                        """
                        INSERT INTO jobs (
                            dedupe_hash, source, company, title, location,
                            remote_policy, url, description, first_seen, last_seen
                        ) VALUES (?, 'manual', ?, ?, ?, 'Remote', '', ?, ?, ?)
                        """,
                        (
                            d_hash,
                            company.strip(),
                            title.strip(),
                            location.strip(),
                            jd_snapshot or "",
                            now_iso,
                            now_iso,
                        ),
                    )
                    resolved_job_id = int(cur.lastrowid)
                    job_description = jd_snapshot or ""
            else:
                raise StoreError("Provide a job ID, --url, or --manual with --company and --title.")

            existing_app = conn.execute(
                "SELECT id, stage FROM applications WHERE job_id = ?",
                (resolved_job_id,),
            ).fetchone()
            if existing_app is not None:
                raise StoreError(
                    f"Application #{existing_app['id']} already exists for job #{resolved_job_id} (stage: {existing_app['stage']})."
                )

            applied_at: Optional[str] = None
            next_action_at: Optional[str] = None
            if stage_clean == "applied":
                applied_at = now_iso
                next_action_at = utc_now_iso(now_dt + timedelta(days=due_days))
            elif stage_clean in ("screen", "interview"):
                applied_at = now_iso
                next_action_at = utc_now_iso(now_dt + timedelta(days=due_days))

            snapshot = jd_snapshot if jd_snapshot is not None else job_description

            cur = conn.execute(
                """
                INSERT INTO applications (
                    job_id, stage, applied_at, next_action_at,
                    cv_path, cv_sha256, jd_snapshot, match_score, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_job_id,
                    stage_clean,
                    applied_at,
                    next_action_at,
                    norm_cv_path,
                    cv_sha256,
                    snapshot,
                    match_score,
                    notes or "",
                ),
            )
            app_id = int(cur.lastrowid)

            detail_parts = [f"Created application in stage '{stage_clean}'"]
            if cv_sha256:
                detail_parts.append(f"CV sha256={cv_sha256[:12]}")
            conn.execute(
                "INSERT INTO events (application_id, at, kind, detail) VALUES (?, ?, ?, ?)",
                (app_id, now_iso, "stage_change", "; ".join(detail_parts)),
            )
            if notes:
                conn.execute(
                    "INSERT INTO events (application_id, at, kind, detail) VALUES (?, ?, ?, ?)",
                    (app_id, now_iso, "note", notes),
                )

        return self.get_application(app_id)  # type: ignore[return-value]

    def move_application(
        self,
        app_id: int,
        new_stage: str,
        note: Optional[str] = None,
        due_days: int = 7,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Moves an application to a new stage and records a stage_change event."""
        stage_clean = new_stage.strip().lower()
        if stage_clean not in VALID_STAGES:
            raise StoreError(
                f"Invalid stage '{new_stage}'. Must be one of: {', '.join(VALID_STAGES)}"
            )

        now_dt = now or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        now_iso = utc_now_iso(now_dt)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, stage, applied_at FROM applications WHERE id = ?",
                (app_id,),
            ).fetchone()
            if row is None:
                raise StoreError(f"Application #{app_id} not found.")

            old_stage = row["stage"]
            applied_at = row["applied_at"]

            if stage_clean == "applied" and not applied_at:
                applied_at = now_iso

            next_action_at: Optional[str] = None
            if stage_clean in ACTIVE_STAGES:
                next_action_at = utc_now_iso(now_dt + timedelta(days=due_days))

            conn.execute(
                """
                UPDATE applications
                SET stage = ?,
                    applied_at = ?,
                    next_action_at = ?
                WHERE id = ?
                """,
                (stage_clean, applied_at, next_action_at, app_id),
            )

            detail = f"{old_stage} -> {stage_clean}"
            if note:
                detail += f": {note}"
            conn.execute(
                "INSERT INTO events (application_id, at, kind, detail) VALUES (?, ?, ?, ?)",
                (app_id, now_iso, "stage_change", detail),
            )
            if note:
                conn.execute(
                    "UPDATE applications SET notes = CASE WHEN notes = '' THEN ? ELSE notes || '\n' || ? END WHERE id = ?",
                    (note, note, app_id),
                )

        return self.get_application(app_id)  # type: ignore[return-value]

    def add_note(
        self,
        app_id: int,
        note_text: str,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Appends a timestamped note to an application and logs an event."""
        if not note_text or not note_text.strip():
            raise StoreError("Note text cannot be empty.")

        now_iso = utc_now_iso(now)
        clean_note = note_text.strip()

        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, notes FROM applications WHERE id = ?",
                (app_id,),
            ).fetchone()
            if row is None:
                raise StoreError(f"Application #{app_id} not found.")

            updated_notes = f"{row['notes']}\n{clean_note}".strip() if row["notes"] else clean_note
            conn.execute(
                "UPDATE applications SET notes = ? WHERE id = ?",
                (updated_notes, app_id),
            )
            conn.execute(
                "INSERT INTO events (application_id, at, kind, detail) VALUES (?, ?, ?, ?)",
                (app_id, now_iso, "note", clean_note),
            )

        return self.get_application(app_id)  # type: ignore[return-value]

    def get_application(self, app_id: int) -> Optional[Dict[str, Any]]:
        """Returns full application dict including joined job fields and event history."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    a.*,
                    j.company, j.title, j.location, j.remote_policy,
                    j.source, j.external_id, j.url, j.dedupe_hash,
                    j.salary_min, j.salary_max, j.currency,
                    j.posted_at, j.first_seen, j.last_seen, j.closed_at
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.id = ?
                """,
                (app_id,),
            ).fetchone()
            if row is None:
                return None

            events = conn.execute(
                "SELECT id, application_id, at, kind, detail FROM events WHERE application_id = ? ORDER BY at ASC, id ASC",
                (app_id,),
            ).fetchall()

            data = dict(row)
            data["events"] = [dict(e) for e in events]
            return data

    def list_applications(self, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists applications joined with job details, optionally filtered by stage."""
        if stage is not None:
            stage_clean = stage.strip().lower()
            if stage_clean not in VALID_STAGES:
                raise StoreError(
                    f"Invalid stage '{stage}'. Must be one of: {', '.join(VALID_STAGES)}"
                )
        else:
            stage_clean = None

        with self._connect() as conn:
            query = """
                SELECT
                    a.*,
                    j.company, j.title, j.location, j.remote_policy,
                    j.source, j.url, j.closed_at,
                    (SELECT MAX(at) FROM events e WHERE e.application_id = a.id) AS last_event_at
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
            """
            params: Tuple[Any, ...] = ()
            if stage_clean is not None:
                query += " WHERE a.stage = ?"
                params = (stage_clean,)
            query += " ORDER BY a.id DESC"

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_due_applications(
        self,
        days: int = 7,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Finds applications needing follow-up.
        By default checks `applied` (and active follow-up stages) where either:
        - `applied_at` is at least `days` old (elapsed >= days), OR
        - `next_action_at` <= now (when using default schedule).
        When `days` is specified cleanly against `applied_at`, ensures deterministic date math.
        """
        now_dt = now or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)

        cutoff_dt = now_dt - timedelta(days=days)
        due_list: List[Dict[str, Any]] = []

        for app in self.list_applications():
            if app["stage"] not in ("applied", "screen", "interview"):
                continue

            applied_dt = parse_iso(app.get("applied_at"))
            next_dt = parse_iso(app.get("next_action_at"))

            is_due = False
            days_elapsed = 0
            if applied_dt is not None:
                days_elapsed = int((now_dt - applied_dt).total_seconds() // 86400)
                if applied_dt <= cutoff_dt:
                    is_due = True
            if next_dt is not None and next_dt <= now_dt and days == 7:
                is_due = True

            if is_due:
                app_copy = dict(app)
                app_copy["days_since_applied"] = days_elapsed
                due_list.append(app_copy)

        return due_list

    def get_ghost_candidates(
        self,
        days: int = 21,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Suggests active applications with no response/update for >= `days` days.
        Does NOT modify application stage automatically.
        """
        now_dt = now or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        cutoff_dt = now_dt - timedelta(days=days)

        candidates: List[Dict[str, Any]] = []
        for app in self.list_applications():
            if app["stage"] not in ACTIVE_STAGES:
                continue

            last_activity = parse_iso(app.get("last_event_at")) or parse_iso(app.get("applied_at"))
            if last_activity is not None and last_activity <= cutoff_dt:
                stale_days = int((now_dt - last_activity).total_seconds() // 86400)
                item = dict(app)
                item["stale_days"] = stale_days
                candidates.append(item)

        return candidates

    def export_applications(self, fmt: str = "csv") -> str:
        """Exports tracked applications as CSV or Markdown table."""
        fmt_clean = fmt.strip().lower()
        if fmt_clean not in ("csv", "md"):
            raise StoreError(f"Unsupported export format '{fmt}'. Must be 'csv' or 'md'.")

        apps = self.list_applications()
        headers = [
            "id",
            "stage",
            "company",
            "title",
            "source",
            "location",
            "applied_at",
            "next_action_at",
            "cv_sha256",
            "match_score",
            "url",
            "notes",
        ]

        if fmt_clean == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator="\n")
            writer.writerow(headers)
            for a in apps:
                writer.writerow(
                    [
                        a.get("id", ""),
                        a.get("stage", ""),
                        a.get("company", ""),
                        a.get("title", ""),
                        a.get("source", ""),
                        a.get("location", ""),
                        a.get("applied_at") or "",
                        a.get("next_action_at") or "",
                        (a.get("cv_sha256") or "")[:12],
                        a.get("match_score") if a.get("match_score") is not None else "",
                        a.get("url") or "",
                        (a.get("notes") or "").replace("\n", " "),
                    ]
                )
            return buf.getvalue()

        # Markdown export
        md_headers = ["ID", "Stage", "Company", "Title", "Source", "Applied", "CV Hash", "URL"]
        lines = [
            "| " + " | ".join(md_headers) + " |",
            "| " + " | ".join("---" for _ in md_headers) + " |",
        ]
        for a in apps:
            applied_str = (a.get("applied_at") or "")[:10]
            cv_short = (a.get("cv_sha256") or "")[:8]
            row = [
                str(a.get("id", "")),
                str(a.get("stage", "")),
                str(a.get("company", "")).replace("|", "\\|"),
                str(a.get("title", "")).replace("|", "\\|"),
                str(a.get("source", "")),
                applied_str or "-",
                cv_short or "-",
                str(a.get("url") or "-"),
            ]
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines) + "\n"
