# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0-dev] - 2026-11-25

### Added
- **Template Outreach & Cover Generator (`feat/cover-outreach`):**
  - Added `careerforge/core/cover.py` and plain-text `hook -> proof -> ask` templates in `careerforge/data/templates/` (`cover.txt`, `cold_email.txt`, `linkedin.txt`, `follow_up.txt`) bundled in `pyproject.toml`.
  - Enforced word/character caps (`cover` target 150-200 words, strict <= 200 cap; `linkedin` <= 300 chars), explicit `<<FILL: ...>>` markers for unknown slots, automatic `anti_ai_engine.audit_text()` validation, and `--type follow-up --app <id>` SQLite lookup from `forge track` (plus tip in `forge track due`).
  - Wired `forge cover` CLI, added `docs/COVER.md`, updated `docs/PRIVACY_MODEL.md`, and added `tests/test_cover.py`.
- **Interview Prep & STAR Story Bank (`feat/interview-star`):**
  - Added `careerforge/core/interview.py` with honest STAR drafting from `profile.yaml` (`TODO: fill in` placeholders, metric-first prioritization, zero fabricated narrative), `stories.yaml` persistence via `platformdirs` (`CAREERFORGE_DATA_DIR` / `CAREERFORGE_STORIES` overrides), and 8-category behavioral coverage auditing.
  - Added curated role question banks in `careerforge/data/questions/` (`general.yaml`, `data.yaml`, `backend.yaml`, `frontend.yaml`) and bundled them in `pyproject.toml`.
  - Wired `forge interview` subcommands (`draft`, `add`, `list`, `edit`, `coverage`, `practice` with `--seed`, `--timer`, and Anti-AI `--audit`), plus `docs/INTERVIEW.md`.

## [0.3.0-dev] - 2026-11-25

### Added
- **Remote Geo-Eligibility, Lever Scraper & Tailor Diff (`feat/remote-eligibility-lever`):**
  - Added heuristic geo-restriction rule engine (`careerforge/core/eligibility.py` & `careerforge/data/eligibility_rules.yaml`) with sentence-level false-positive guards, restriction precedence over generic "worldwide" labels, `--my-country` applicant verdicts, standalone `forge eligibility`, and integration into `forge match` & `forge scrape`.
  - Implemented `LeverScraper` (`careerforge/scrapers/lever_scanner.py`) over `BaseScraper` with live-verified company slugs (`kinsta`, `palantir`, `spotify`, `doxel`, `hevodata`, `zoox`, `wealthsimple`, `shieldai`).
  - Added `forge tailor --diff` itemized bullet scoring table (`skill_score`, `metric_score`, `token_overlap_score`, `weight_score`).
- **Schema v2 & Local Analytics (`forge report`, `forge ghost`, `forge salary`):**
  - Added schema v2 migration tracking `description_hash` and `description_changed_at` in `jobs`.
  - Implemented `forge report` for cumulative funnel conversion rates (`saved` to `offer`), CV SHA-256 performance comparison, terminal sparklines, `--since` filtering, and small-sample warnings.
  - Implemented `forge ghost` heuristic Ghost Risk scoring (`Low`/`Medium`/`High`) with explicit "not proof" caveats and itemized signal breakdown.
  - Implemented `forge salary` calculating `min`, `p25`, `median`, `p75`, `max` per currency with user-supplied `--rates` YAML conversion, selection-bias disclosure, and small-sample warnings.
- **Local SQLite Job & Application Store (`careerforge/core/store.py`):**
  - Implemented stdlib `sqlite3` persistence with `platformdirs` user data path and `CAREERFORGE_DB` environment override.
  - Added `PRAGMA foreign_keys = ON` on every connection and versioned schema migrations via `PRAGMA user_version`.
  - Created `jobs`, `applications`, and `events` tables recording SHA-256 CV hashes, JD snapshots, and full stage change logs.
- **Application Tracking CLI (`forge track`):**
  - Added `add`, `list`, `move`, `note`, `show`, `due`, `ghosted` (suggestion-only), and `export` (`--csv`/`--md`) subcommands with `--json` output and stable exit codes.
  - Updated `forge scrape --save` to upsert postings into SQLite and safely set `closed_at` only on boards fetched without errors.
- **Optional Kanban TUI (`forge track board`):**
  - Added interactive Textual board under optional extra `careerforge[tui]`.

## [0.2.0] - 2026-11-25

### Added
- **ATS Parser Fragility Checker (`forge ats-sim`):**
  - 100% offline inspection engine identifying structural, layout, encoding, and typographic flaws that break resume text extractors.
  - 13 comprehensive checks:
    - `TEXT_EXTRACT`: Plain text extraction verification with hard cap (max 20) on image scans.
    - `SECTIONS`: Standard section heading detection across Experience, Education, Skills, and Summary.
    - `CONTACT`: Core contact validation (Email, Phone, LinkedIn) with hard cap (max 50) on missing contact info.
    - `COLUMNS`: Multi-column layout detection via horizontal bounding box clustering in PDF and `w:cols` XML analysis in DOCX.
    - `DOCX_STRUCT`: Document structure analysis flagging `w:txbxContent` text boxes and nested tables.
    - `HEADER_FOOTER`: Header and footer containment check ensuring contact info is present in the main document body.
    - `UNICODE`: Detection of typographic ligatures (U+FB00–U+FB06) and hidden zero-width characters (U+200B, U+FEFF, etc.).
    - `ICON_GLYPHS`: Private Use Area (PUA) character detection for decorative icon fonts that extract as replacement glyphs.
    - `FONTS`: Font embedding and ATS-safe font family verification (Calibri, Arial, Times New Roman, etc.).
    - `DATES`: Consistency checks across date representations (flags mixed written month and numeric formats).
    - `PAGE_COUNT`: Document length verification (target: exactly 1 page).
    - `PARSER_AGREEMENT`: Dual-parser consistency comparison between `pdfminer.six` and `pypdf`.
    - `FIELD_RECOVERY`: Entity discovery comparison against `profile.yaml` with missing field reporting.
  - Rich table CLI visualization with check status, overall score (0–100), and actionable fix recommendations.
  - `--json` machine-readable output format with standard exit codes (0 for pass, 1 for needs attention, 2 for error).
  - `--check` flag on `forge apply` and `forge tailor` to automatically audit generated PDFs.
- **Dependencies:**
  - Added `pdfminer.six>=20231228` (MIT) and `pypdf>=4.0.0` (BSD) to core dependencies.
  - Added `rich>=13.0.0` for terminal table formatting.

## [0.1.0] - 2026-11-23

### Added
- **Offline Knapsack CV Tailoring (`forge tailor`):**
  - Re-ranks and selects highest-relevance experience bullets and projects matching a specific Job Description.
  - Automatically optimizes and exports guaranteed 1-page tailored `.docx` and `.pdf` resumes completely offline.
- **ATS Keyword Match & Gap Analysis (`forge match`):**
  - Compares candidate master profile against any Job Description using the 250+ skill ontology in `skills.yaml`.
  - Reports match percentage, matched skills, and highlighted missing keywords.
- **Direct Employer ATS Dork Generator (`forge dorks`):**
  - Generates targeted Google search queries and direct links for Greenhouse, Lever, Ashby, Workable, and Hacker News.
- **Package Architecture:** Standard Python package structure installable via `pip install .` or `pip install -e ".[dev]"`.
- **Universal ATS CV Engine:** 1-page layout optimization using LibreOffice headless (cross-platform default) and Microsoft Word COM (Windows fast-path).
- **Research-Backed Anti-AI Linguistic Audit (`forge audit`):**
  - Modular YAML rules in `careerforge/data/anti_ai_rules.yaml` with Rule IDs (`AI-001` through `AI-005`, `CADENCE-001`).
  - Empirical citations: *Kobak et al. (Science Advances 2024)*, *Reinhart et al. (PNAS 2025)*, *Juzek & Ward (ACL 2025)*.
- **Scraper Plugin Architecture:**
  - `BaseScraper` abstract base class with User-Agent politeness, automatic exponential backoff retries, and rate limiting.
  - Pydantic `JobPosting` unified schema.
  - Scrapers for Greenhouse public APIs, Ashby APIs, and Remotive public API.
  - Deterministic SHA256 dedup signature helper.
- **System Doctor Command (`forge doctor`):**
  - Platform detection and environment diagnostics.
  - Copy-paste installation hints for missing PDF backends (Windows winget, macOS brew, Linux apt).
  - Machine-readable `--json` flag and deterministic exit codes.
- **Privacy Enforcement:**
  - Automated `pytest-socket` tests proving audit, profile loader, and CV builder open zero network sockets.
  - Complete `.pre-commit-config.yaml` blocking accidental commits of `profile.yaml`.
- **Community Infrastructure:**
  - GitHub Actions CI matrix testing across Ubuntu, Windows, and macOS on Python 3.10, 3.11, and 3.12.
  - GitHub issue templates, pull request template, Code of Conduct, and Security policy.
