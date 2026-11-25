# Local Application Tracker (`forge track`)

`forge track` stores job postings and application history in a local SQLite database (`careerforge.db`) located in your system user data directory (via `platformdirs`). It runs strictly offline using Python's built-in `sqlite3` library with zero network requests.

## Database Path & Configuration
- Default location: system user data directory (`careerforge/careerforge.db`).
- Override environment variable: set `CAREERFORGE_DB=/path/to/db.sqlite` to isolate databases for testing or multiple job searches.

## Schema Overview
- `jobs`: Stores deduplicated postings (`dedupe_hash`), source, company, title, location, salary fields, URL, description, `first_seen`, `last_seen`, and `closed_at`.
- `applications`: Tracks one application per job (`saved`, `applied`, `screen`, `interview`, `offer`, `rejected`, `ghosted`), along with `applied_at`, `next_action_at`, submitted `cv_path`, `cv_sha256`, `jd_snapshot`, `match_score`, and `notes`.
- `events`: Appends an audit trail entry whenever an application changes stage or receives a note.

## Commands
- `forge scrape --save`: Upserts scraped openings into `jobs`. Sets `closed_at` on older jobs ONLY when the corresponding `(source, company)` board succeeded in that scrape run, avoiding false closures when a board fails to load.
- `forge track add [<job-id> | --url <URL> | --manual --company <C> --title <T>] [--cv <path>] [--jd <path|text>] [--stage saved|applied|...]`: Starts tracking a job and computes the CV SHA-256 digest when `--cv` is provided.
- `forge track list [--stage <stage>] [--json]`: Lists tracked applications.
- `forge track move <id> <stage> [--note "..."]`: Updates application stage and logs an event.
- `forge track note <id> "<text>"`: Appends a note and logs an event.
- `forge track show <id> [--json]`: Displays full job metadata, CV hash, JD snapshot preview, and event timeline.
- `forge track due [--days 7] [--json]`: Lists active applications past the follow-up threshold (default 7 days from application).
- `forge track ghosted [--days 21] [--json]`: Suggests active applications with no updates for at least 21 days. Never auto-moves stages.
- `forge track export --csv|--md [--out <path>]`: Exports applications to CSV or Markdown.
- `forge track board`: Opens the interactive Kanban terminal UI (requires `pip install careerforge[tui]`). Keyboard shortcuts: arrow keys or `h/j/k/l` navigate, `[` / `]` or `Shift+Arrows` move cards across stages, `Enter` toggles details, `q` quits.

## Limitations
1. Single-user local SQLite database: concurrent multi-writer access across multiple background terminals is not designed for heavy parallelism.
2. Follow-up (`due`) and stagnant (`ghosted`) windows rely strictly on timestamps recorded in `applications` and `events`. External email responses are not automatically synced.
3. Automatic `closed_at` closure only applies to company boards where full job listings are fetched cleanly in a single API call (`Greenhouse`, `Ashby`, `Lever`); category feeds (`Remotive`) do not close older entries automatically.
