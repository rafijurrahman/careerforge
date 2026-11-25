<div align="center">

<img src="assets/hero-banner.svg" width="100%" alt="CareerForge — Universal Job Application Engine" />

<br/>

[![CI](https://github.com/rafijurrahman/careerforge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rafijurrahman/careerforge/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20(Supported)%20%7C%20Linux%20(Community)-lightgrey?style=flat-square)
![Privacy](https://img.shields.io/badge/Telemetry-Zero%20%28100%25%20Local%29-purple?style=flat-square)

**A local, open-source job application and career automation engine. Works for any role. Runs on your machine. Your data stays yours.**

[Quick Start](#quick-start) · [Available Now](#-available-now) · [Roadmap](#-planned-features-roadmap) · [Portals](#job-portals) · [Architecture](docs/ARCHITECTURE.md) · [Research](docs/RESEARCH.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## What is CareerForge?

Most career tools are closed cloud services that lock your resume behind monthly subscriptions, sell candidate data, and generate synthetic text full of recognizable AI buzzwords (*delve*, *pivotal*, *seamless*, *tapestry*).

CareerForge is an open-source, local-first alternative. You define one master profile in local YAML, and CareerForge optimizes clean, single-page ATS-readable resumes (`.docx` and `.pdf`), audits your writing against computational linguistics findings, and scans public job boards without requiring third-party accounts or cloud APIs.

```
                  ┌─────────────────────────────────────────┐
                  │          Local profile.yaml             │
                  └────────────────────┬────────────────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                ▼                      ▼                      ▼
       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
       │   forge apply   │    │   forge audit   │    │  forge scrape   │
       │  1-Page Fitting │    │ Research Anti-AI│    │ Greenhouse/Ashby│
       │ LibreOffice/COM │    │ Heuristic Rules │    │    Remotive     │
       └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
                ▼                      ▼                      ▼
         1-Page ATS CV          Clean Human Voice       Targeted Roles
```

---

## 🖥️ Platform Support & PDF Engines

| Operating System | Support Level | Supported PDF Engines | Verification Status |
|---|:---:|:---:|---|
| **Windows 10 / 11** | **Officially Supported** | Microsoft Word COM (Fast-path) + LibreOffice | Verified in GitHub Actions CI |
| **macOS 12+ (Monterey+)** | **Officially Supported** | LibreOffice Headless (Required) | Verified in GitHub Actions CI |
| **Linux (Ubuntu, Fedora, etc.)** | **Community-Supported** | LibreOffice Headless | Verified in GitHub Actions CI (Ubuntu runner) |

### Installing LibreOffice (Required for macOS, Linux & Non-Word Windows setups)
* **Windows (via winget):**
  ```powershell
  winget install TheDocumentFoundation.LibreOffice
  ```
* **macOS (via Homebrew):**
  ```bash
  brew install --cask libreoffice
  ```
* **Linux (Debian/Ubuntu):**
  ```bash
  sudo apt-get update && sudo apt-get install -y libreoffice-writer
  ```

---

<!--
## Terminal Demo

<div align="center">

![CareerForge Intro](demo/intro.gif)

<br/>

![CareerForge Demo](demo/demo.gif)

</div>

*(To record or update terminal demos locally, run `vhs demo/demo.tape`)*
-->

---

## ⚡ Quick Start

### 1. Install CareerForge

```bash
# Recommended (isolated CLI application):
pipx install git+https://github.com/rafijurrahman/careerforge.git

# Or install from source:
git clone https://github.com/rafijurrahman/careerforge.git
cd careerforge
pip install -e .
```
*(On Windows with Microsoft Word installed, run `pip install -e ".[windows]"` for the optional Word COM fast-path).*

### 2. Verify System Dependencies
```bash
forge doctor
```

### 3. Initialize Your Profile and Tailor Your First CV
```bash
forge init
forge tailor --jd job.txt
forge apply --role-tag "Universal"
```
*(Note: tailor selects and prioritizes bullets from your real master profile; it never invents skills or experience).*

Your optimized 1-page CV is written to `output/YourName_Universal_CV.docx` and `.pdf`.

---

## ⚖️ CareerForge vs. Cloud Resume Tools

| Feature | CareerForge | Cloud AI Resume Builders |
|---|:---:|:---:|
| **Cost** | **100% Free & Open Source (MIT)** | Often subscription-based |
| **Privacy** | **No telemetry. audit/match/tailor/apply never use the network. Only scrape and dorks contact public job sites.** | Resumes stored on company servers |
| **Document Fit** | **Auto-fits to 1 page (grid-search; checked in CI)** | Often overflows to accidental 2nd page |
| **Writing Style** | **Informed by published research on LLM text markers** | Generic synthetic LLM puffery |
| **Job Search** | **Direct Public ATS (Greenhouse, Ashby)** | Middleman affiliate job boards |
| **Extensibility** | **Plugin Scrapers & Modular Rules** | Closed proprietary platform |

---

## 📦 Features

### ✅ Available Now (v0.2.0)

*   **ATS Parser Fragility Checker (`forge ats-sim`):**  
    Inspects PDF and DOCX resume documents for structural, layout, encoding, and typographic flaws that break text extractors (such as scanned image-only PDFs, multi-column layouts, XML text boxes, header/footer trapping, Unicode ligatures, Private Use Area icon font glyphs, date formatting inconsistencies, and dual-parser stream divergence). Operates completely offline without external APIs and generates actionable fix recommendations. *(Note: this is a parser fragility checker, not an emulator of proprietary Workday, Taleo, or Greenhouse ranking algorithms).*
*   **Job-Specific Auto-Tailoring (`forge tailor`):**  
    Uses an offline knapsack algorithm to score and prioritize bullets from your Master Profile based on relevance to a specific Job Description, outputting an optimized 1-page tailored CV without cloud APIs. *(Note: tailor selects from your real master profile; it never invents skills or experience).*
*   **ATS Keyword Match & Gap Analysis (`forge match`):**  
    Analyzes any job description against your candidate profile, calculating an ATS match percentage, listing matched skills, and highlighting missing keywords.
*   **Direct Employer ATS Search Dorks (`forge dorks`):**  
    Generates high-precision search queries for Greenhouse, Lever, Ashby, Workable, and Hacker News to discover live openings directly on employer domains without aggregators.
*   **Automated 1-Page Document Optimizer (`forge apply`):**  
    Uses an iterative grid-search to adjust font scaling, spacing, and margins until your resume strictly fits exactly 1 page. Uses headless LibreOffice as the cross-platform default, with Microsoft Word COM as a Windows fast-path. Supports `--check` to automatically run parser diagnostics after building.
*   **Empirical Anti-AI Linguistic Audit (`forge audit`):**  
    Scans cover letters and resumes against heuristics informed by published research on LLM text markers (Kobak et al. 2024, Reinhart et al. PNAS 2025, Juzek & Ward 2025) and editorial cleanup guidelines to flag stylistic buzzwords (`AI-001`), copula replacements (`AI-002`), robotic transitions (`AI-003`), participial suffixes (`AI-004`), and low-burstiness cadence (`CADENCE-001`).
*   **Public ATS & Remote Job Scrapers (`forge scrape`):**  
    Concurrently scans Greenhouse public APIs, Ashby APIs, and Remotive for matching opportunities with built-in politeness (User-Agent headers, rate limiting, and exponential backoff).
*   **System Diagnostics (`forge doctor`):**  
    Inspects your local environment for Python version, Word COM / LibreOffice availability, profile syntax, and bundled rules. Supports `--json` output with stable exit codes.
*   **Universal Skills Ontology (`careerforge/data/skills.yaml`):**  
    250+ canonical skills and aliases across 12 professional disciplines (Software, Data, Marketing, Accounting/Finance, Sales, Customer Support, HR, Healthcare/Nursing, Design, Project Management, Education, and Operations/Logistics).
*   **Provable Offline Privacy:**  
    Enforced by automated `pytest-socket` tests proving that audit, profile loading, ats-sim, and CV generation execute completely offline without opening network sockets.

### 🗺️ Planned Features (Roadmap)

The following advanced utilities are currently under active design. See [`ROADMAP.md`](ROADMAP.md) for milestones:

*   **`forge track` (Offline SQLite Kanban):**  
    A local terminal UI (TUI) powered by `Textual` for tracking applications (`Saved`, `Applied`, `Interview`, `Offer`, `Ghosted`) with zero cloud dependencies.
*   **`forge ghost` (Stale / Ghost Job Detector):**  
    Calculates Ghost Risk scores based on posting age and repost frequency from ATS APIs.
*   **`forge salary` (Salary Range Intelligence):**  
    Aggregates pay transparency disclosures into local SQLite with currency conversion.
*   **`forge interview` (STAR Story Bank):**  
    Transforms master profile achievement bullets into structured Situation-Task-Action-Result interview talking points with behavioral category coverage tracking.

---

## 🌐 Job Portals

CareerForge defaults to **100% Remote / Worldwide** opportunities so you don't waste time on geo-restricted listings. To add Hybrid or On-site roles in your area, edit `preferred_work_modes` in `profile.yaml`.

For our complete directory of 30+ free remote portals, search dorks, and startup networks, see [`JOB_PLATFORMS.md`](JOB_PLATFORMS.md).

---

## 🤝 Contributing & Community

We actively welcome contributions! Check our [Good First Issues](https://github.com/rafijurrahman/careerforge/issues?q=label%3A%22good+first+issue%22) for tasks ready to pick up.

*   **Want to add a new job board scraper?** Read [`docs/ADDING_A_SCRAPER.md`](docs/ADDING_A_SCRAPER.md).
*   **Want to propose a new linguistic rule?** Open an issue using our [New Rule Template](.github/ISSUE_TEMPLATE/new_audit_rule.yml).
*   **See general guidelines:** Check [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## 🔒 Security & Privacy

Read our complete [Privacy Model](docs/PRIVACY_MODEL.md) and [Security Policy](SECURITY.md). CareerForge does not collect telemetry, track usage, or store your resumes in the cloud.

### Command Network Scope Summary:
| Command | Network Access | Data Sent Over Network |
|---|:---:|---|
| `forge init` | **None** (Offline) | None |
| `forge doctor` | **None** (Offline) | None |
| `forge audit` | **None** (Offline) | None |
| `forge match` | **None** (Offline) | None |
| `forge tailor` | **None** (Offline) | None |
| `forge apply` | **None** (Offline) | None |
| `forge dorks` | **None** (Offline) | Generates local search URLs; zero network calls |
| `forge scrape` | **Read-only public APIs** | Fetches public job postings from Greenhouse, Ashby, and Remotive |

---

## 📄 License

CareerForge is distributed under the [MIT License](LICENSE).
