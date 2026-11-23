# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
