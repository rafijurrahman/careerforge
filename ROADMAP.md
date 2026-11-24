# CareerForge — Engineering Roadmap & Architecture

This document outlines the master architecture, feature milestones, and open-source roadmap for **CareerForge** — the privacy-first, local-first job search and career automation engine.

---

## 🧭 Core Philosophy & Moat
1. **100% Local & Private:** Zero user telemetry, zero cloud tracking, zero data exfiltration. All data stays in `profile.yaml` and local SQLite databases.
2. **Guaranteed 1-Page ATS Engine:** Automatic page-budget optimization via font-scaling and knapsack bullet selection (no 2nd page spills).
3. **Research-Backed Anti-AI Voice:** Enforces empirical linguistic research (*PNAS 2025*, *Science Advances 2024*, *ACL 2025*) to eradicate AI puffery and robotic cadence.
4. **Honesty Guardrail:** CareerForge will never hallucinate, invent fake metrics, or insert skills the candidate does not have.

---

## 🗺️ Release Milestones

### Phase 1: Foundation & Packaging (v0.2)
- [x] Universal ATS CV Generator (`core/cv_builder.py` + `core/page_optimizer.py`)
- [x] Initial Greenhouse, Ashby & Remotive Scrapers (`scrapers/`)
- [x] Curated Free Job Portal Directory (`JOB_PLATFORMS.md`)
- [x] Base CV reference guide (`cv/README.md`)
- [x] Packaging with `pyproject.toml` (`pip install -e .` and `careerforge` / `forge` CLI aliases)
- [x] Rule modularization: Move Anti-AI rules from code to `careerforge/data/anti_ai_rules.yaml` (Rule IDs: `AI-001`, `AI-002`)
- [x] Diagnostic engine: `forge doctor` to inspect Python, Word COM, LibreOffice, and font availability
- [ ] Rich terminal UI (colored diffs, status panels, tabular output)
- [x] Community templates: Issue templates (Bug, New Scraper, New Rule), `CODE_OF_CONDUCT.md`, `SECURITY.md`, `docs/PRIVACY_MODEL.md`

### Phase 2: Extensibility & ATS Simulation (v0.3)
- [ ] **Plugin Scraper Architecture:** `BaseScraper` class with rate limiting, politeness headers, and unified Pydantic `JobPosting` schema.
- [ ] **Additional Scrapers:** Lever public postings API, Workable, Hacker News "Who is Hiring?" monthly threads.
- [ ] **`forge ats-sim` (ATS Parser Simulator):**
  - Section extraction test (Experience, Education, Skills, Contact).
  - Reading order test (verifying columns/tables don't scramble text).
  - Unicode/ligature/special character sanitizer.
  - Generates 0-100 ATS Readability Score.
- [ ] `--json` output across all commands for automated agent/script integration.

### Phase 3: Intelligent Matching & Knapsack Tailoring (v0.2.0)
- [x] **`skills.yaml` (Skill Ontology):** Curated mapping of skills and aliases across 12 disciplines (`k8s` → `kubernetes`, `postgres` → `postgresql`).
- [x] **`forge match` (Keyword Gap Analysis):** Offline ontology matching comparing Master Profile against Job Descriptions with match percentage and missing skills.
- [x] **`forge tailor` (Budgeted Knapsack Selection):**
  - Scores bullets by relevance to the JD, metric presence, and weight.
  - Automatically selects optimal bullet combinations that maximize relevance score while strictly fitting the 1-page line budget.
- [x] **`forge dorks` (Direct Employer Search):** High-precision Google ATS queries targeting Greenhouse, Lever, Ashby, Workable, and Hacker News.
- [ ] **Remote-Eligibility Filter:** Flags hidden restrictions (e.g. "US Citizen only" or "US timezone required" disguised as "Worldwide").

### Phase 4: Local Application Tracking & Analytics (v0.5)
- [ ] **`forge track` (Offline SQLite Kanban):**
  - Zero-config local SQLite schema (`applications`, `events`).
  - Terminal UI (TUI) via `Textual` for moving cards across stages (`Saved`, `Applied`, `Screen`, `Interview`, `Offer`, `Rejected`, `Ghosted`).
  - Automatic follow-up alerts and ghost warnings (21+ days without response).
- [ ] **`forge report` (Pipeline Analytics):**
  - Visual terminal charts showing application-to-interview conversion rates.
  - CV version A/B test response analytics.

### Phase 5: Deep Intelligence & Interview Prep (v0.6)
- [ ] **`forge ghost` (Stale / Ghost Job Detector):**
  - Tracks job age and repost frequency to calculate Ghost Risk Score (Low, Medium, High).
- [ ] **`forge salary` (Salary Intelligence):**
  - Aggregates salary disclosures from ATS APIs into local SQLite with currency conversion.
- [ ] **`forge interview` (STAR Story Bank):**
  - Turns profile achievement bullets into structured STAR (Situation, Task, Action, Result) interview answers.
  - Behavioral coverage matrix (highlights missing story categories like Conflict, Failure, Leadership).

### Phase 6: Ecosystem & Distribution (v1.0)
- [ ] PyPI distribution (`pipx install careerforge`)
- [ ] Docker container with pre-configured headless LibreOffice for identical cross-platform rendering.
- [ ] Windows Scoop / Winget package.
- [ ] Documentation site with MkDocs Material.
