<div align="center">

<img src="assets/hero-banner.svg" width="100%" alt="CareerForge — Universal Job Application Engine" />

<br/>

[![CI](https://github.com/careerforge/careerforge/actions/workflows/ci.yml/badge.svg)](https://github.com/careerforge/careerforge/actions)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![Privacy](https://img.shields.io/badge/Telemetry-Zero%20%28100%25%20Local%29-purple?style=flat-square)

**A local, open-source job application and career automation engine. Works for any role. Runs on your machine. Your data stays yours.**

[Quick Start](#quick-start) · [Available Now](#-available-now) · [Roadmap](#-planned-features-roadmap) · [Portals](#job-portals) · [Architecture](docs/ARCHITECTURE.md) · [Research](docs/RESEARCH.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## What is CareerForge?

Most career tools are closed cloud services that lock your resume behind monthly subscriptions, sell candidate data, and generate synthetic text full of recognizable AI buzzwords (*delve*, *pivotal*, *seamless*, *tapestry*).

CareerForge is an open-source, local-first alternative. You define one master profile in local YAML, and CareerForge optimizes clean, single-page ATS-readable resumes (`.docx` and `.pdf`), audits your writing against empirical computational linguistics papers, and scans public job boards without requiring third-party accounts or cloud APIs.

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
       │ LibreOffice/COM │    │ PNAS & ACL Rules│    │    Remotive     │
       └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
                ▼                      ▼                      ▼
         1-Page ATS CV          Clean Human Voice       Targeted Roles
```

---

## 🖥️ Platform Support & PDF Engines

| Operating System | Support Level | Supported PDF Engines | Verification Status |
|---|:---:|:---:|---|
| **Windows 10 / 11** | **Officially Supported** | Microsoft Word COM (Fast-path) + LibreOffice | Full 1-page fit & test coverage |
| **macOS 12+ (Monterey+)** | **Officially Supported** | LibreOffice Headless (Required) | Verified in GitHub Actions CI |
| **Linux (Ubuntu, Fedora, etc.)** | **Community-Supported** | LibreOffice Headless | Unit tests verified; page-fit community-supported |

### Installing LibreOffice (Required for macOS & Non-Word Windows setups)
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

## ⚡ 3-Command Quick Start

### 1. Install CareerForge
```bash
git clone https://github.com/careerforge/careerforge.git
cd careerforge
pip install -e .
```
*(On Windows with Microsoft Word installed, run `pip install -e ".[windows]"` for the optional Word COM fast-path).*

### 2. Verify System Dependencies
```bash
forge doctor
```

### 3. Initialize Your Profile and Build Your First CV
```bash
forge init
forge apply --role-tag "Universal"
```
Your optimized 1-page CV is written to `output/YourName_Universal_CV.docx` and `.pdf`.

---

## ⚖️ CareerForge vs. Cloud Resume Tools

| Feature | CareerForge | Cloud AI Resume Builders |
|---|:---:|:---:|
| **Cost** | **100% Free & Open Source (MIT)** | $15 – $40 / month subscription |
| **Privacy** | **100% Local (Zero Telemetry)** | Resumes stored on company servers |
| **Document Fit** | **Guaranteed 1-Page Layout** | Often overflows to accidental 2nd page |
| **Writing Style** | **Research-Backed Anti-AI Voice** | Generic synthetic LLM puffery |
| **Job Search** | **Direct Public ATS (Greenhouse, Ashby)** | Middleman affiliate job boards |
| **Extensibility** | **Plugin Scrapers & Modular Rules** | Closed proprietary platform |

---

## 📦 Features

### ✅ Available Now (v0.1.0)

*   **Job-Specific Auto-Tailoring (`forge tailor`):**  
    Uses an offline knapsack algorithm to score and prioritize bullets from your Master Profile based on relevance to a specific Job Description, outputting an optimized 1-page tailored CV without cloud APIs.
*   **ATS Keyword Match & Gap Analysis (`forge match`):**  
    Analyzes any job description against your candidate profile, calculating an ATS match percentage, listing matched skills, and highlighting missing keywords.
*   **Direct Employer ATS Search Dorks (`forge dorks`):**  
    Generates high-precision Google search queries for Greenhouse, Lever, Ashby, Workable, and Hacker News to discover live openings directly on employer domains without aggregators.
*   **Automated 1-Page Document Optimizer (`forge apply`):**  
    Uses an iterative grid-search to adjust font scaling, spacing, and margins until your resume strictly fits exactly 1 page. Uses headless LibreOffice as the cross-platform default, with Microsoft Word COM as a Windows fast-path.
*   **Empirical Anti-AI Linguistic Audit (`forge audit`):**  
    Scans cover letters and resumes against peer-reviewed computational linguistics findings (*PNAS 2025*, *Science Advances 2024*, *ACL 2025*) to eradicate AI puffery (`AI-001`), copula avoidance (`AI-002`), robotic transitions (`AI-003`), participial suffixes (`AI-004`), and low-burstiness cadence (`CADENCE-001`).
*   **Public ATS & Remote Job Scrapers (`forge scrape`):**  
    Concurrently scans Greenhouse public APIs, Ashby APIs, and Remotive for matching opportunities with built-in politeness (User-Agent headers, rate limiting, and exponential backoff).
*   **System Diagnostics (`forge doctor`):**  
    Inspects your local environment for Python version, Word COM / LibreOffice availability, profile syntax, and bundled rules. Supports `--json` output with stable exit codes.
*   **Universal Skills Ontology (`careerforge/data/skills.yaml`):**  
    250+ canonical skills and aliases across 12 professional disciplines (Software, Data, Marketing, Accounting/Finance, Sales, Customer Support, HR, Healthcare/Nursing, Design, Project Management, Education, and Operations/Logistics).
*   **Provable Offline Privacy:**  
    Enforced by automated `pytest-socket` tests proving that audit, profile loading, and CV generation execute completely offline without opening network sockets.

### 🗺️ Planned Features (Roadmap)

The following advanced utilities are currently under active design. See [`ROADMAP.md`](ROADMAP.md) for milestones:

*   **`forge tailor` (Budgeted Knapsack Auto-Tailoring):**  
    Selects the optimal subset of bullet points from your master profile to maximize relevance to a specific Job Description while strictly fitting the 1-page line budget.
*   **`forge ats-sim` (ATS Parser Simulator):**  
    Extracts text and evaluates section recognition, reading order, ligature sanitization, and contact extraction to generate a pre-application ATS Readability Score (0-100).
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

## 🤝 Contributing & Good First Issues

We actively welcome contributions!

*   **Want to add a new job board scraper?** Read [`docs/ADDING_A_SCRAPER.md`](docs/ADDING_A_SCRAPER.md).
*   **Want to propose a new linguistic rule?** Open an issue using our [New Rule Template](.github/ISSUE_TEMPLATE/new_audit_rule.yml).
*   **See general guidelines:** Check [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

### Good First Issues for New Contributors:
1. `scraper`: Add Lever public postings API scraper (`jobs.lever.co`)
2. `scraper`: Add Workable public API scanner (`apply.workable.com`)
3. `scraper`: Add SmartRecruiters public API integration
4. `skills`: Expand DevOps skill aliases in `careerforge/data/skills.yaml`
5. `skills`: Expand Healthcare specialized certifications in `skills.yaml`
6. `rules`: Add detection rule for passive voice over-reliance
7. `rules`: Add rule for corporate buzzword nominalizations (`utilization of`)
8. `docs`: Translate README into Bengali, Spanish, and Hindi
9. `cli`: Add colored diff output for `forge audit` using Rich
10. `cli`: Add `--export-csv` flag to `forge scrape`

---

## 🔒 Security & Privacy

Read our complete [Privacy Model](docs/PRIVACY_MODEL.md) and [Security Policy](SECURITY.md). CareerForge will never collect analytics or transmit your profile to external servers.

---

## 📄 License

CareerForge is distributed under the [MIT License](LICENSE).
