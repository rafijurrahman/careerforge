# Contributing to CareerForge

Thank you for your interest in contributing to CareerForge! We welcome contributions to our scrapers, anti-AI linguistic engine, ATS templates, and documentation.

---

## 🛠️ Development Setup

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/rafijurrahman/careerforge.git
   cd careerforge
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Editable Package with Dev Dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-Commit Hooks:**
   ```bash
   pre-commit install
   ```

---

## 🧪 Running Tests & Quality Checks

Run the automated test suite locally before pushing:
```bash
# Run pytest with network disabled (tests run completely offline)
pytest -v

# Run linter
ruff check .

# Run diagnostics
forge doctor
```

---

## 📝 How to Add an Anti-AI Linguistic Rule

All linguistic rules are stored as data in [`careerforge/data/anti_ai_rules.yaml`](careerforge/data/anti_ai_rules.yaml).

### Requirements for New Rules:
1. **Rule ID:** Must be unique (e.g. `AI-006`).
2. **Category:** e.g. `puffery`, `copula_avoidance`, `transition_signposts`, `participial_suffix`.
3. **Severity:** `warn` or `error`.
4. **Citation (Mandatory):** Must cite a peer-reviewed paper (*PNAS*, *ACL*, *Science Advances*), corpus study, or Wikipedia AI Cleanup finding. Speculative or subjective rules will not be accepted.
5. **Pattern:** Valid Python regex string.
6. **Suggestions:** Practical, natural human phrasing alternatives.
7. **Test Cases:** Add positive and negative test cases in `tests/test_audit.py`.

---

## 🌐 How to Add a Job Board Scraper

See the full worked tutorial in [`docs/ADDING_A_SCRAPER.md`](docs/ADDING_A_SCRAPER.md).

### Scraping Ethics & Politeness Policy:
* **Official APIs Preferred:** Scrapers should query public, unauthenticated JSON endpoints (e.g., Greenhouse or Ashby public posting APIs).
* **Respect Robots.txt & ToS:** We do not bypass paywalls, solve CAPTCHAs, or scrape authenticated user portals.
* **Politeness Headers:** Every scraper must inherit from `BaseScraper`, which injects the `CareerForge/<version>` User-Agent, timeouts, and rate limits.
* **Contract Fixtures Required:** Every scraper PR must include a recorded JSON fixture in `tests/fixtures/` and an offline test in `tests/test_scrapers.py`.

---

## 🔒 Privacy & Safety Guarantee

CareerForge is strictly privacy-first.
* Never commit `profile.yaml` or real personal documents.
* Never add telemetry or analytics tracking.
* All PRs must pass the offline `pytest-socket` test suite.
