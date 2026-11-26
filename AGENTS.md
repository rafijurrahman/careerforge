# AGENTS.md — Working with AI Coding Assistants

CareerForge works with local AI coding assistants, including Google Antigravity, Claude Code, OpenAI Codex, and Cursor. This document explains how agents should interact with the codebase and how users can prompt them.

---

## Supported AI Assistants

### 1. Google Antigravity
Antigravity operates with terminal and file system access.
- **Workflow:**
  1. Have Antigravity run `forge setup` or edit `profile.yaml` directly with your verified career background.
  2. Paste a job description into chat and ask Antigravity to match your profile using `forge match --jd posting.txt`.
  3. Ask Antigravity to generate a tailored resume via `forge tailor --jd posting.txt --output output/cv.pdf`.
  4. Run `forge audit --file output/cv.pdf` to audit candidate statements against anti-AI puffery heuristics.
- **Sample User Prompt:**
  > "Read AGENTS.md and my profile.yaml. I saved a job description to job.txt. Run forge match on it, select relevant bullets from my profile, and run forge tailor to build a 1-page CV. Then run forge audit on the generated text."

---

### 2. Claude Code (Anthropic)
Claude Code executes shell commands and reads local files.
- **Workflow:**
  - Reads `profile.yaml` and repository documentation.
  - Runs `forge` CLI commands via bash tools.
  - Helps add new company boards to `careerforge/scrapers/board_registry.py`.
- **Sample User Prompt:**
  > "Inspect AGENTS.md and run forge doctor. If healthy, tailor my CV for the job posting in posting.txt using forge tailor."

---

### 3. OpenAI Codex, Cursor, and GitHub Copilot
These tools assist with code navigation, autocomplete, and terminal execution.
- Edit `careerforge/data/anti_ai_rules.yaml` to adjust or add custom linting heuristics.
- Extend scraper classes in `careerforge/scrapers/`.
- Use the built-in terminal to run `forge` commands.

---

## Agent Guidelines & Ground Rules

1. **Zero Metric Invention:**
   Never invent unverified degrees, job titles, companies, or quantitative statistics. Every bullet point must derive from the user's `profile.yaml`.
2. **Deterministic Tool Execution:**
   Always run the built-in `forge` commands (`forge match`, `forge tailor`, `forge ats-sim`, `forge audit`) rather than writing custom one-off scripts.
3. **Privacy First:**
   `profile.yaml` contains personal contact information. It is `.gitignore`d by default and must never be committed to source control.
