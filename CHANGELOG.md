# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0-dev] - 2026-11-25

### Added
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
