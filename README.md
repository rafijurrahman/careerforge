<div align="center">

<img src="assets/hero-banner.svg" width="100%" alt="CareerForge — The job search that runs on your machine. Pip the courier bird carries an application along a flight path to a destination pin." />

<br/>

[![CI](https://github.com/rafijurrahman/careerforge/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rafijurrahman/careerforge/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux%20(Community)-lightgrey?style=flat-square)
![No Telemetry](https://img.shields.io/badge/Telemetry-Zero%20(100%25%20Local)-purple?style=flat-square)

<p><strong>Local-first job search toolkit: tailor your CV to any job description, check it reads cleanly, and track every application. No cloud, no subscription, no telemetry.</strong></p>

<p align="center">
  <img src="demo/hero.gif" width="95%" alt="Terminal recording showing forge tailor and forge ats-sim commands running on local machine" /><br/>
  <em>Real terminal recording, fictional data (Alex Rivera). Nothing leaves your machine.</em>
</p>

<p>
  <a href="#why-careerforge">Why CareerForge</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#requirements">Requirements</a> &bull;
  <a href="#installation">Installation</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#command-cheat-sheet">Command Cheat Sheet</a> &bull;
  <a href="#privacy-and-integrity-commitment">Privacy</a> &bull;
  <a href="#frequently-asked-questions">FAQ</a> &bull;
  <a href="#roadmap-and-status">Roadmap</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

</div>

---

## Why CareerForge?

Most job search tools rely on closed cloud services. They charge recurring subscriptions, retain candidate resumes on remote servers, and generate text full of generic phrases that automated parsers and recruiters flag.

CareerForge offers a local, open-source alternative:

1. **Manual CV editing takes too much time:** Adjusting bullet points for each posting is slow, and small edits often push resumes onto an accidental second page.
2. **Job listings hide geographical limits:** Postings with "Worldwide Remote" headers often bury US work authorization or state restrictions deep in paragraph text.
3. **AI-generated outreach sounds artificial:** Standard language model outputs share predictable vocabularies and flat cadences that make cover letters sound formulaic.
4. **Application tracking drifts out of sync:** Spreadsheets require constant manual upkeep, while cloud trackers store personal work histories on third-party databases.

CareerForge solves these issues directly on your computer. It selects your strongest real achievements for each role, ensures your resume stays on a single page, checks file formats for common parser traps, and tracks your job pipeline in a local SQLite database.

### Comparison: CareerForge vs Typical Cloud Tools

| Dimension | CareerForge | Typical Cloud Career Portals |
| :--- | :--- | :--- |
| **Pricing** | Free and open source (MIT license) | Often subscription-based (\$15–\$30/month) |
| **Data Storage** | Local SQLite and local YAML on your machine | Remote third-party servers and cloud databases |
| **Skill Integrity** | Uses only real experience from your profile | Often invents or fabricates unverified skills |
| **Offline Operation** | Yes (network used only for job board scraping) | Requires constant internet and cloud accounts |
| **Candidate Privacy** | Zero telemetry, zero analytics scripts | User behavioral tracking and session logs |

---

## Features

CareerForge covers every stage of the job search workflow across six core categories: **Find**, **Match**, **Build**, **Track & Analyze**, **Prepare**, and **Setup**.

Skills matching is bounded across 12 domains: Software Engineering, Data & Analytics, Cloud & DevOps, Machine Learning & AI, Cybersecurity, Product Management, Quality Assurance, Database Administration, Systems & Networks, Mobile Development, Technical Writing, and Project Management.

---

### 1. Find

Search public job boards or generate search queries without sharing your search activity.

#### `forge scrape`
*Search public job boards for openings matching your target roles.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Checking multiple job portals by hand is slow and repetitive.
* **How it works:** Queries unauthenticated public APIs from Greenhouse, Ashby, Lever, and Remotive over HTTPS. Filters postings by role titles, seniority level, and remote eligibility rules.
* **Your benefit:**
  * Aggregates openings across four major ATS platforms in one command.
  * Filters out senior or lead titles automatically when targeting junior roles.
  * Stores results directly into your local database with `--save`.
* **Command:**
  ```powershell
  # Search remote Data Analyst roles and save to local SQLite
  forge scrape --roles "Data Analyst" --my-country BD --save
  ```
* **Sample output:**
  ```text
  🔎 Searching for: Data Analyst
     Work mode filter: Remote
     Sources: Greenhouse | Ashby | Lever | Remotive

  Found 14 matching roles across 4 platforms:
  [1] Nexus Systems — Data Analyst (Ashby | Remote)
  [2] Crestline Health Labs — Reporting Analyst (Greenhouse | Remote)
  Saved 14 jobs to local database.
  ```
* **Limitation:** Covers Greenhouse, Ashby, Lever, and Remotive; employers using Workable or custom portals require separate search.

</details>

#### `forge dorks`
*Generate targeted Google search queries for direct employer job boards.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Aggregator sites often repost expired listings or scrape roles without employer links.
* **How it works:** Constructs search strings targeting direct employer subdomains (`boards.greenhouse.io`, `jobs.lever.co`, `jobs.ashbyhq.com`, `apply.workable.com`, and Hacker News threads) entirely offline.
* **Your benefit:**
  * Find fresh listings directly on employer job boards before aggregators index them.
  * Add custom skill keywords and location constraints.
  * Zero network requests sent from the CLI tool itself.
* **Command:**
  ```powershell
  # Generate direct search links for Backend Engineer
  forge dorks "Backend Engineer" --location "remote" --skills "Python,PostgreSQL"
  ```
* **Sample output:**
  ```text
  🔎 Direct Employer ATS Search Dorks for 'Backend Engineer' (remote)

  1. [Greenhouse] Greenhouse-hosted direct job boards
     Query: site:boards.greenhouse.io "Backend Engineer" "remote" "Python,PostgreSQL"
     URL:   https://www.google.com/search?q=site%3Aboards.greenhouse.io+...

  2. [Ashby] Ashby high-growth startup listings
     Query: site:jobs.ashbyhq.com "Backend Engineer" "remote" "Python,PostgreSQL"
     URL:   https://www.google.com/search?q=site%3Ajobs.ashbyhq.com+...
  ```
* **Limitation:** Prints search URLs for your browser; it does not scrape Google search results directly.

</details>

---

### 2. Match

Evaluate job postings against your skill profile and check for hidden geographical limitations.

<p align="center">
  <img src="demo/eligibility.gif" width="95%" alt="Terminal recording of forge eligibility detecting hidden US restrictions" /><br/>
  <em>Real terminal recording, fictional data.</em>
</p>

#### `forge match`
*Score how closely your real skills match a job description.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Figuring out whether your profile fits a job posting usually requires line-by-line reading.
* **How it works:** Extracts technical requirements from the job description and compares them against your `profile.yaml` using a curated ontology of aliases across 12 disciplines.
* **Your benefit:**
  * Displays match percentage based on skills you have verified in your profile.
  * Lists missing skills so you know what technical gaps exist.
  * Evaluates country eligibility when `--my-country` is provided.
* **Command:**
  ```powershell
  forge match --jd job.txt --profile profile.yaml --my-country BD
  ```
* **Sample output:**
  ```text
  Match Score:     87.5%
  Matched Skills:  Docker, FastAPI, Go, Kafka, PostgreSQL, Python
  Missing Skills:  Kubernetes, GraphQL
  Can Apply (BD):  Yes (Worldwide Remote)
  ```
* **Limitation:** Matches explicit skills and synonyms from `skills.yaml`; it cannot infer unstated or implied skills.

</details>

#### `forge eligibility`
*Detect hidden geographical and visa restrictions in job postings.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Job postings labeled "Worldwide Remote" often hide US citizenship or residency clauses in the text.
* **How it works:** Scans the text using regex rules targeting residency, security clearances, citizenship clauses, and country restrictions.
* **Your benefit:**
  * Avoid spending time tailoring resumes for roles that exclude your region.
  * Cites exact rule IDs and excerpts where restrictions were found.
  * Supports country code checking with `--my-country`.
* **Command:**
  ```powershell
  forge eligibility --jd examples/job_restricted.txt --my-country BD
  ```
* **Sample output:**
  ```text
  ================================================================
  🌍 Remote Geo-Eligibility Check (Heuristic)
  ================================================================
  Status:          Restricted
  Notice:          Heuristic eligibility estimate from text rules.
  Regions/Flags:   US, VISA_RESTRICTED
  Can Apply (BD):  No (heuristic: restricted to US)

  Evidence Snippets:
    • [ELIG-US-01 | US | restricted] - Must reside in the United States and be authorized to work in the US without visa sponsorship.
  ================================================================
  ```
* **Limitation:** Rule-based heuristic; unusual phrasing or novel legal terms may not trigger a flag.

</details>

---

### 3. Build

Generate single-page ATS-ready resumes, verify file structures, and audit prose.

#### `forge tailor`
*Select your most relevant real achievements to build a 1-page resume.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Fitting your most relevant achievements onto a single page without manual formatting is difficult.
* **How it works:** Uses a knapsack selection algorithm to rank bullet points by keyword relevance, metric presence, and weight. Fits text into a strict one-page budget using subtle font scaling.
* **Your benefit:**
  * Generates clean `.docx` and `.pdf` files strictly formatted for single-page reading.
  * Never invents skills or metrics; draws exclusively from your `profile.yaml`.
  * Use `--diff` to see exact score breakdowns for why each bullet was selected or dropped.
* **Command:**
  ```powershell
  forge tailor --jd examples/job_backend.txt --diff
  ```
* **Sample output:**
  ```text
  ============================================================
  ✨ Tailored 1-Page ATS CV Successfully Generated!
  ============================================================
  Candidate:            Alex Rivera
  Initial Match:        100.0%
  Tailored Match:       100.0%
  Matched Skills:       Docker, FastAPI, Go, GraphQL, Kafka, Kubernetes, PostgreSQL, Python
  ------------------------------------------------------------
  DOCX:                 output/tailored/Alex_Rivera_Tailored_CV.docx
  PDF:                  output/tailored/Alex_Rivera_Tailored_CV.pdf
  Pages:                1 | Font Scale: 1.06
  Backend Engine:       Word COM
  ============================================================
  ```
* **Limitation:** Requires Microsoft Word (Windows) or LibreOffice (macOS/Linux) installed for PDF generation.

</details>

#### `forge apply`
*Build a baseline universal resume from your profile without tailoring to a specific posting.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** You need a general-purpose, single-page resume ready for networking or broad applications.
* **How it works:** Renders your master profile bullets directly into standard professional ATS templates and scales typography to fit exactly one page.
* **Your benefit:**
  * Outputs both `.docx` and `.pdf` files immediately.
  * Automatically verifies page budget and line counts.
  * Runs parser checks on the output when `--check` is passed.
* **Command:**
  ```powershell
  forge apply --profile profile.yaml --check
  ```
* **Sample output:**
  ```text
  Generating universal baseline CV for Alex Rivera...
  Output written to: output/Alex_Rivera_Universal_CV.pdf (1 page)
  Running ATS parser fragility check...
  Score: 95/100 (PASSED)
  ```
* **Limitation:** Renders your top default profile bullets without job description weighting.

</details>

#### `forge ats-sim`
*Check your resume for parser fragility traps that cause automated systems to drop data.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Resumes often look fine to human eyes but scramble inside automated parsers due to multi-column flows, tables, or non-standard fonts.
* **How it works:** Uses `pdfminer.six` and `pypdf` to run 13 deterministic diagnostic checks, testing text stream extraction, section headers, contact extraction, font encodings, and field recovery.
* **Your benefit:**
  * Catches formatting issues before submitting your resume.
  * Generates a 0–100 Parseability Score with specific fix recommendations.
  * Checks entity recovery against your `profile.yaml` when provided.
* **Command:**
  ```powershell
  forge ats-sim output/tailored/Alex_Rivera_Tailored_CV.pdf --profile examples/profile.example.yaml
  ```
* **Sample output:**
  ```text
  ATS Parser Fragility Diagnostic: Alex_Rivera_Tailored_CV.pdf
  ┌──────────────────┬─────────────────────────────┬────────┬────────────────────────────────────────────┐
  │ Check ID         │ Name                        │ Status │ Diagnostic Detail                          │
  ├──────────────────┼─────────────────────────────┼────────┼────────────────────────────────────────────┤
  │ TEXT_EXTRACT     │ Text Extraction             │ PASS   │ Successfully extracted 1450 characters.    │
  │ SECTIONS         │ Standard Headings           │ WARN   │ Found 2/4 headings. Missing: Skills.       │
  │ CONTACT          │ Contact Information         │ PASS   │ Found: Email, Phone, LinkedIn.             │
  │ COLUMNS          │ Multi-Column Layout         │ PASS   │ Single-column linear layout verified.      │
  │ PAGE_COUNT       │ Page Count                  │ PASS   │ Document verified to be exactly 1 page.    │
  │ FIELD_RECOVERY   │ Profile Entity Recovery     │ PASS   │ Recovered 17/18 (94.4%) profile entities.  │
  └──────────────────┴─────────────────────────────┴────────┴────────────────────────────────────────────┘
  Overall Parseability Score: 95 / 100 - PASSED (ATS Parser Safe)
  ```
* **Limitation:** Checks parser readability heuristics; it does not simulate proprietary enterprise algorithms (such as Workday or Taleo).

</details>

#### `forge audit`
*Flag AI puffery words and metronomic sentence cadences using published linguistics heuristics.*

<p align="center">
  <img src="demo/audit.gif" width="95%" alt="Terminal recording of forge audit analyzing sample AI text" /><br/>
  <em>Real terminal recording, fictional data.</em>
</p>

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Candidate statements and cover letters written with AI assistants often read with predictable, robotic styles that recruiters notice.
* **How it works:** Scans text against rules informed by computational linguistics research (*PNAS 2025*, *Science Advances 2024*, *COLING 2025*) and Wikipedia cleanup standards. Flags vocabulary overrepresentation, copula avoidance, and metronomic sentence rhythm.
* **Your benefit:**
  * Flags overused AI buzzwords, weak verbs, and inflated corporate filler.
  * Measures sentence length variance to avoid monotone paragraphs.
  * Suggests direct, active human phrasing for every flagged item.
* **Command:**
  ```powershell
  forge audit --file examples/sample_ai_text.txt
  ```
* **Sample output:**
  ```text
  ============================================================
  🛡️ Anti-AI Linguistic Audit Report
  ============================================================
  Compliant:            NO ⚠️
  Total Issues:         19
  Sentence Count:       5
  Average Sentence:     14.6 words
  Burstiness Cadence:   LOW_VARIANCE (Uniform AI cadence detected)

  Findings:
    1. [WARN] AI-001: 'delve' → Suggestion: explore, study, analyze
    2. [WARN] AI-001: 'realm' → Suggestion: Use plain, active human verbs.
    3. [ERROR] AI-002: 'stands as a' → Suggestion: is
    4. [WARN] AI-003: 'furthermore' → Suggestion: also, and
  ============================================================
  ```
* **Limitation:** Flags stylistic patterns commonly associated with LLM generation; flagged words are not absolute proof that text was generated by AI.

</details>

---

### 4. Track & Analyze

Manage your applications locally and review conversion analytics.

<p align="center">
  <img src="demo/track.gif" width="95%" alt="Terminal recording of forge track list, forge ghost, and forge report" /><br/>
  <em>Real terminal recording, fictional data.</em>
</p>

#### `forge track`
*Track applications, record follow-ups, and run a terminal Kanban board.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Keeping track of where you applied, which CV version you submitted, and when to follow up is messy across multiple spreadsheets.
* **How it works:** Stores applications, stage transitions, and notes in a local zero-configuration SQLite database (`careerforge.db`). Records submitted CV file paths and SHA-256 hashes.
* **Your benefit:**
  * Move applications through standard stages: `saved`, `applied`, `screen`, `interview`, `offer`, `rejected`, `ghosted`.
  * Check applications due for follow-up with `forge track due`.
  * Export your pipeline to CSV or Markdown with `forge track export`.
  * Launch an interactive terminal Kanban board with `forge track board` (requires `careerforge[tui]`).
* **Command:**
  ```powershell
  # Add an application and inspect pipeline
  forge track add --manual --company "Nexus Systems" --title "Backend Engineer" --cv output/tailored/Alex_Rivera_Tailored_CV.pdf
  forge track list
  ```
* **Sample output:**
  ```text
                             Tracked Job Applications
  ┌────┬───────────┬────────────────┬──────────────────────────┬────────────┬──────────────┐
  │ ID │ Stage     │ Company        │ Title                    │ Applied    │ CV SHA       │
  ├────┼───────────┼────────────────┼──────────────────────────┼────────────┼──────────────┤
  │ 1  │ applied   │ Nexus Systems  │ Backend Engineer         │ 2026-11-26 │ a0d6fff71c34 │
  │ 2  │ interview │ Crestline Health  │ Analytics Engineer       │ 2026-11-15 │ a0d6fff71c34 │
  │ 3  │ rejected  │ Riverbank Tech │ Backend Systems Engineer │ 2026-10-28 │ a5174d2155b3 │
  └────┴───────────┴────────────────┴──────────────────────────┴────────────┴──────────────┘
  ```
* **Limitation:** Manages your pipeline locally; it does not automatically submit forms on external websites.

</details>

#### `forge report`
*Review funnel conversion rates and CV version performance.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Job seekers rarely know which resume variant converts best or where candidates drop off in their search.
* **How it works:** Aggregates your local SQLite event history to compute stage conversion rates, average response intervals, and response rates grouped by CV SHA-256 hash and job source.
* **Your benefit:**
  * Visual ASCII funnel chart showing step-by-step conversion.
  * Response rate comparison across different resume versions.
  * Average days to first employer response.
* **Command:**
  ```powershell
  forge report --since 30d
  ```
* **Sample output:**
  ```text
                     Application Funnel Report
  ┌──────────────┬─────────┬───────────┬────────────────────────┐
  │ Stage        │   Count │    Step % │ Bar                    │
  ├──────────────┼─────────┼───────────┼────────────────────────┤
  │ saved        │       3 │    100.0% │ ████████████████████   │
  │ applied      │       3 │    100.0% │ ████████████████████   │
  │ screen       │       1 │     33.3% │ ███████░░░░░░░░░░░░░   │
  │ interview    │       1 │    100.0% │ ███████░░░░░░░░░░░░░   │
  │ offer        │       0 │      0.0% │ ░░░░░░░░░░░░░░░░░░░░   │
  └──────────────┴─────────┴───────────┴────────────────────────┘
  Funnel Sparkline: ██▃▃▁
  Average Days to First Response: 11.0 days
  ```
* **Limitation:** High-variance warning is displayed when sample size is smaller than 10 applications.

</details>

#### `forge ghost`
*Estimate stale listing and ghost job risks using listing age and repost data.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Many job postings remain open for months or get reposted repeatedly without active hiring.
* **How it works:** Analyzes listing age, refresh intervals, description hash changes, and title patterns to assign a 0–100 Ghost Risk score (Low, Medium, High).
* **Your benefit:**
  * Prioritize fresh postings over stale listings.
  * View detailed reasons explaining the risk score.
  * Inspect specific job IDs with `forge ghost <id>`.
* **Command:**
  ```powershell
  forge ghost --top 3
  ```
* **Sample output:**
  ```text
                            Ghost Risk Heuristic Audit
  ┌─────┬────────┬───────┬──────────────────────┬────────────────────────┬──────────────────────┐
  │ ID  │ Risk   │ Score │ Company              │ Title                  │ Reasons              │
  ├─────┼────────┼───────┼──────────────────────┼────────────────────────┼──────────────────────┤
  │ 2   │ Medium │    40 │ Harbor Freight Tech  │ Senior Backend Eng     │ Posting age 68 days; │
  │     │        │       │                      │                        │ description static.  │
  │ 5   │ Medium │    35 │ Cascade Logistics    │ Platform Data Eng      │ Age 75 days; no      │
  │     │        │       │                      │                        │ refresh in 75 days.  │
  └─────┴────────┴───────┴──────────────────────┴────────────────────────┴──────────────────────┘
  ```
* **Limitation:** Heuristic risk estimation; it is not definitive proof of an employer's hiring intent.

</details>

#### `forge salary`
*Analyze disclosed salary ranges from stored job postings.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Disclosed compensation figures vary widely and are hard to compare across listings.
* **How it works:** Extracts structured salary minimums and maximums from saved job postings and computes local percentiles (Min, P25, Median, P75, Max). Supports optional currency conversion via user YAML.
* **Your benefit:**
  * Realistic compensation expectations before interview negotiations.
  * Filter by role keyword or currency code.
  * Supply your own exchange rates with `--rates rates.yaml` without external API calls.
* **Command:**
  ```powershell
  forge salary --role "Backend" --currency USD
  ```
* **Sample output:**
  ```text
                           Disclosed Compensation Bands
  ┌──────────┬───────┬───────────┬───────────┬───────────┬───────────┬───────────┐
  │ Currency │ Count │       Min │       P25 │    Median │       P75 │       Max │
  ├──────────┼───────┼───────────┼───────────┼───────────┼───────────┼───────────┤
  │ USD      │     5 │    85,000 │   105,000 │   115,000 │   120,000 │   160,000 │
  └──────────┴───────┴───────────┴───────────┴───────────┴───────────┴───────────┘
  ```
* **Limitation:** Reflects only postings that explicitly disclose numerical compensation ranges.

</details>

---

### 5. Prepare

Prepare for interviews and draft professional outreach without AI boilerplate.

#### `forge interview`
*Draft honest STAR outlines from your profile and practice role questions.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Behavioral interview questions are difficult to answer clearly without structured preparation.
* **How it works:** Converts bullet points from your `profile.yaml` into structured STAR (Situation, Task, Action, Result) outlines. Facts come strictly from your profile; missing context is left as `TODO:` markers.
* **Your benefit:**
  * Never invents details; prompts you to supply genuine missing context.
  * Audits coverage across 8 behavioral categories (leadership, conflict, failure, etc.) with `forge interview coverage`.
  * Practice with curated questions and run style checks with `forge interview practice --audit`.
* **Command:**
  ```powershell
  # Draft STAR outlines and practice with behavioral questions
  forge interview draft --limit 2
  forge interview practice --role backend --seed 42
  ```
* **Sample output:**
  ```text
  ┌─ Draft #1: Apex Cloud Systems: Reduced p95 API response times from 840ms to ─┐
  │ Situation: Senior Backend Engineer at Apex Cloud Systems (Jan 2023 – Present)│
  │ Task:      TODO: fill in                                                     │
  │ Action:    Reduced p95 API response times from 840ms to 210ms by introducing │
  │            Redis caching and query indexing.                                 │
  │ Result:    TODO: fill in (profile cites metrics: 840ms, 210ms)               │
  └──────────────────────────────────────────────────────────────────────────────┘
  ```
* **Limitation:** Provides question banks and outlines; candidate reflection is required to complete the context.

</details>

#### `forge cover`
*Draft concise outreach templates with explicit fill markers and Anti-AI style checks.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** Writing cold outreach or cover notes often results in either generic templates or bloated AI essays.
* **How it works:** Fills clean outreach templates with matching skills from your profile and the target job description. Automatically checks drafts against `forge audit` rules and flags any unfilled `<<FILL>>` markers.
* **Your benefit:**
  * Supports 4 outreach types: `cover`, `cold-email`, `linkedin`, and `follow-up`.
  * Guarantees concise word counts (150–200 words) and plain language.
  * Verified to pass Anti-AI linguistic checks out of the box.
* **Command:**
  ```powershell
  forge cover --jd examples/job_backend.txt --company "Nexus Systems" --role "Senior Backend Engineer"
  ```
* **Sample output:**
  ```text
  ┌──────────── cover draft (168 words, 1109 chars | Anti-AI: PASS) ────────────┐
  │ Hi <<FILL: hiring manager name>>,                                           │
  │                                                                             │
  │ I am applying for the Senior Backend Engineer role at Nexus Systems. Your   │
  │ focus on Docker, FastAPI, Go lines up closely with my recent work.          │
  │                                                                             │
  │ Built REST and GraphQL endpoints in Python and FastAPI serving 120,000      │
  │ daily active users. Architected event-driven ingestion pipeline in Go and   │
  │ Kafka processing 14,000 messages per second.                                │
  │ ...                                                                         │
  └─────────────────────────────────────────────────────────────────────────────┘
  Manual fill required (1): <<FILL: hiring manager name>>
  ```
* **Limitation:** Generates grounded drafts; personalization for hiring manager details must be filled manually.

</details>

---

### 6. Setup & Diagnostics

Initialize candidate data and verify system dependencies.

#### `forge init`
*Initialize your local candidate profile.*

<details>
<summary><strong>View command details</strong></summary>

* **Problem solved:** Writing a structured YAML profile from scratch is prone to formatting mistakes.
* **How it works:** Launches an interactive wizard that prompts for contact details, target roles, technical skills, and employment achievements. Writes a structured `profile.yaml` to your working directory.
* **Command:**
  ```powershell
  forge init
  ```
* **Limitation:** Runs interactively via terminal input.

</details>

#### `forge doctor`
*Diagnose your local system configuration, dependencies, and engines.*

<details>
<summary><strong>View command details and sample output</strong></summary>

* **Problem solved:** It is hard to know whether Python versions, document engines, or bundled datasets are configured properly.
* **How it works:** Checks the Python environment, LibreOffice or Word COM availability, bundled anti-AI rules, skill ontology files, and `profile.yaml` validity.
* **Command:**
  ```powershell
  forge doctor
  ```
* **Sample output:**
  ```text
  ============================================================
  🩺 CareerForge Doctor — System Diagnostics
  ============================================================
  [PASS ✅] Python Version: 3.12.10 (Requires >= 3.10)
  [PASS ✅] Profile: 'profile.yaml' valid.
  [PASS ✅] Document Engine: Microsoft Word COM (Fast-path)
  [PASS ✅] Anti-AI Rules: Bundled in package
  [PASS ✅] Skills Ontology: Bundled in package
  ============================================================
  ```
* **Limitation:** Validates local dependencies; it does not test network endpoints.

</details>

---

## Requirements

CareerForge runs on Windows, macOS, and Linux.

### System Prerequisites

| Component | Windows | macOS | Linux (Community) |
| :--- | :--- | :--- | :--- |
| **Python** | Python 3.10, 3.11, 3.12, or 3.13 | Python 3.10, 3.11, 3.12, or 3.13 | Python 3.10, 3.11, 3.12, or 3.13 |
| **Package Tool** | `pipx` (recommended) or `pip` | `pipx` (recommended) or `pip` | `pipx` (recommended) or `pip` |
| **Primary PDF Engine** | Microsoft Word COM (`careerforge[windows]`) | LibreOffice (`brew install --cask libreoffice`) | LibreOffice (`libreoffice-writer`) |
| **Fallback PDF Engine**| LibreOffice (`winget install TheDocumentFoundation.LibreOffice`) | None needed | None needed |
| **Interactive TUI** | Optional: `careerforge[tui]` | Optional: `careerforge[tui]` | Optional: `careerforge[tui]` |

### Command Requirements Matrix

| Command | Python Core | PDF Engine (Word / LibreOffice) | Terminal TUI | Network Access |
| :--- | :---: | :---: | :---: | :---: |
| `forge init` / `setup` / `doctor` | Required | Optional | No | Offline |
| `forge scrape` | Required | No | No | Public ATS APIs |
| `forge dorks` | Required | No | No | Offline (prints URLs) |
| `forge match` / `eligibility` | Required | No | No | Offline |
| `forge tailor` / `apply` | Required | Required | No | Offline |
| `forge ats-sim` | Required | No | No | Offline |
| `forge audit` | Required | No | No | Offline |
| `forge track` (`list`/`add`/`move`/etc.) | Required | No | No | Offline |
| `forge track board` | Required | No | Required (`careerforge[tui]`) | Offline |
| `forge report` / `ghost` / `salary` | Required | No | No | Offline |
| `forge interview` / `cover` | Required | No | No | Offline |

---

## Installation

We recommend installing CareerForge through `pipx` so it runs in an isolated environment available across your entire system.

### Option A: Windows (PowerShell)

1. **Verify Python version (requires Python >= 3.10):**
   ```powershell
   python --version
   ```
2. **Install pipx and update PATH:**
   ```powershell
   python -m pip install --user pipx
   python -m pipx ensurepath
   ```
   *Close and reopen your terminal after running ensurepath.*
3. **Verify document engine:**
   * If you have Microsoft Word installed, you already have the fastest conversion engine.
   * If you do not have Microsoft Word, install LibreOffice:
     ```powershell
     winget install TheDocumentFoundation.LibreOffice
     ```
4. **Install CareerForge:**
   ```powershell
   pipx install git+https://github.com/rafijurrahman/careerforge.git
   ```
5. **(Optional) Enable Word COM fast-path or TUI board:**
   ```powershell
   # If you use Microsoft Word:
   pipx inject careerforge pywin32

   # If you want the interactive Kanban board:
   pipx inject careerforge "careerforge[tui]"
   ```
6. **Verify installation:**
   ```powershell
   forge --version
   # Expected output: careerforge 0.5.1

   forge doctor
   ```

---

### Option B: macOS (Terminal)

1. **Verify Python version (requires Python >= 3.10):**
   ```bash
   python3 --version
   ```
2. **Install pipx and update PATH:**
   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```
   *Close and reopen your terminal.*
3. **Install LibreOffice (required for PDF export on macOS):**
   ```bash
   # Install via Homebrew (https://brew.sh)
   brew install --cask libreoffice
   ```
4. **Install CareerForge:**
   ```bash
   pipx install git+https://github.com/rafijurrahman/careerforge.git
   ```
5. **(Optional) Enable interactive Kanban board:**
   ```bash
   pipx inject careerforge "careerforge[tui]"
   ```
6. **Verify installation:**
   ```bash
   forge --version
   # Expected output: careerforge 0.5.1

   forge doctor
   ```

---

### Option C: Developer Installation

If you want to contribute, modify rules, or run test suites locally:

```bash
git clone https://github.com/rafijurrahman/careerforge.git
cd careerforge

# Create and activate virtual environment
python -m venv .venv

# Windows activation:
.venv\Scripts\Activate.ps1
# macOS/Linux activation:
source .venv/bin/activate

# Install editable package with development dependencies
pip install -e ".[dev,windows,tui]"

# Run offline test suite
pytest -v --disable-socket -m "not office"
```

---

### Upgrading and Uninstalling

```bash
# Upgrade to latest repository revision
pipx upgrade careerforge

# Uninstall CareerForge completely
pipx uninstall careerforge
```

---

### Local Data Locations

CareerForge uses your operating system's standard local application directory (via `platformdirs`). No data is sent to external servers:

* **Windows:** `%LOCALAPPDATA%\careerforge\` (contains `careerforge.db`, `stories.yaml`)
* **macOS / Linux:** `~/.local/share/careerforge/` (contains `careerforge.db`, `stories.yaml`)
* **Environment Overrides:** You can redirect storage anytime using environment variables:
  * `CAREERFORGE_DATA_DIR=/path/to/custom/dir`
  * `CAREERFORGE_DB=/path/to/custom/db.sqlite`

To wipe all stored applications and history, delete the `careerforge.db` file from the directory listed above.

---

### Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `forge: command not found` | The pipx binary path is not in your system PATH. | Run `python -m pipx ensurepath`, close, and reopen your terminal. |
| `LibreOffice executable not found` | LibreOffice is not installed or not in standard paths. | Windows: `winget install TheDocumentFoundation.LibreOffice`<br/>macOS: `brew install --cask libreoffice` |
| `PowerShell Execution Policy` | Windows blocks script activation in new venvs. | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`. |
| `UnicodeEncodeError` in Windows console | Windows console code page is not set to UTF-8. | Add `$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8` to PowerShell profile. |
| `macOS Developer Verification on LibreOffice` | macOS Gatekeeper flags first launch of LibreOffice. | Open LibreOffice once manually from Applications and click "Open". |
| `Word COM Automation Error` | Word process hung or `pywin32` missing. | Run `pipx inject careerforge pywin32` or pass `--engine libreoffice`. |

---

## Quick Start

Get your local career pipeline running in five minutes:

### 1. Initialize your candidate profile
```powershell
forge init
```
*Creates `profile.yaml` in your current directory. Alternatively, copy `examples/profile.example.yaml` to experiment with fictional data.*

> **Security Warning:** Your `profile.yaml` contains personal contact details and salary history. It is `.gitignore`d by default. Never commit your personal `profile.yaml` to a public repository.

### 2. Verify your local environment
```powershell
forge doctor
```
*Confirms your Python version, PDF conversion engine, and rule files.*

### 3. Tailor a resume to a job description
```powershell
# Save a job description to job.txt, then run:
forge tailor --jd examples/job_backend.txt
```
*Generates a 1-page `.docx` and `.pdf` inside `output/tailored/`.*

### 4. Check resume parseability
```powershell
forge ats-sim output/tailored/Alex_Rivera_Tailored_CV.pdf
```
*Runs 13 parser diagnostic checks and returns an overall parseability score.*

### 5. Add the application to your local tracker
```powershell
forge track add --manual --company "Nexus Systems" --title "Senior Backend Engineer" --cv output/tailored/Alex_Rivera_Tailored_CV.pdf
```
*Records the application stage and stores a SHA-256 fingerprint of the submitted PDF.*

### 6. Review your application list
```powershell
forge track list
```
*Displays all active applications, submission dates, and interview stages.*

---

## Command Cheat Sheet

All commands and their network requirements are documented below. This table strictly matches [docs/PRIVACY_MODEL.md](docs/PRIVACY_MODEL.md):

| Command | Action | Network Used? | External Domains |
| :--- | :--- | :---: | :--- |
| `forge init` / `setup` | Create local `profile.yaml` interactively | **No** | None |
| `forge doctor` | Verify local Python, engines, and rules | **No** | None |
| `forge scrape` | Search public ATS job boards | **Yes** | `boards-api.greenhouse.io`, `api.ashbyhq.com`, `api.lever.co`, `remotive.com` |
| `forge dorks` | Print employer search URLs for your browser | **No** | None (prints URLs offline) |
| `forge match` | Score skill overlap against a job description | **No** | None |
| `forge eligibility` | Scan text for remote geographical restrictions | **No** | None |
| `forge tailor` | Rank profile bullets into a 1-page resume | **No** | None |
| `forge apply` | Render baseline 1-page resume | **No** | None |
| `forge ats-sim` | Check PDF/DOCX for parser fragility traps | **No** | None |
| `forge audit` | Check prose for AI style markers and cadence | **No** | None |
| `forge track` | Manage SQLite applications and follow-ups | **No** | None |
| `forge report` | Summarize funnel conversion analytics | **No** | None |
| `forge ghost` | Calculate heuristic Ghost Risk score on stored jobs | **No** | None |
| `forge salary` | Aggregate disclosed compensation percentiles | **No** | None |
| `forge interview` | Draft STAR outlines and practice prompts | **No** | None |
| `forge cover` | Generate template outreach with Anti-AI check | **No** | None |

---

## Privacy and Integrity Commitment

### 1. No Telemetry and Verified Offline Operation
CareerForge contains zero tracking pixels, zero analytics libraries, and zero cloud reporting hooks. All data processing runs on your local CPU. Our test suite enforces network isolation via `pytest-socket` across test modules (`tests/test_privacy.py`, `tests/test_matcher.py`, `tests/test_ats_sim.py`, `tests/test_tailor.py`).

### 2. Candidate Honesty Guardrails
CareerForge never fabricates skills, never creates artificial employer metrics, and never invents qualifications you do not possess. Unstated context in interview drafts is left with explicit `TODO:` markers, and cover notes include `<<FILL>>` tags for candidate review.

### 3. Clear Heuristic Disclaimers
* `forge ats-sim` is a parser fragility checker that tests formatting cleanliness. It does not simulate proprietary enterprise algorithms (such as Workday or Taleo).
* `forge ghost`, `forge eligibility`, and `forge salary` provide rule-based estimates to help you prioritize your time; they do not represent binding statements of employer intent.
* `forge audit` flags stylistic markers commonly associated with LLM generation; flagged words are stylistic suggestions, not proof of AI generation.

### 4. Transparent Network Scope
CareerForge is offline-first. Only `forge scrape` and `forge dorks` interact with external job platforms (`forge scrape` queries public APIs; `forge dorks` formats search queries locally without sending HTTP requests).

### 5. Research-Informed Design
Stylistic checks are informed by published computational linguistics research, including Kobak et al. (*Science Advances*, 2024), Reinhart et al. (*PNAS*, 2025), and Juzek & Ward (*COLING*, 2025). Full citations and analysis are documented in [docs/RESEARCH.md](docs/RESEARCH.md).

### 6. Notice of Concept Visuals
The concept diagrams in this documentation are visual workflow illustrations created to depict the software's operations. Real terminal recordings are explicitly labeled alongside them.

---

## Frequently Asked Questions

<details>
<summary><strong>Does CareerForge guarantee my CV will pass an ATS?</strong></summary>

No. No software can guarantee ATS passage because different employers use different parser configurations, manual recruiter filters, and candidate review criteria. CareerForge ensures your file is free from common technical flaws (such as multi-column stream scrambling, missing standard headings, and non-standard font encodings) so automated parsers read your text cleanly.
</details>

<details>
<summary><strong>Where does my resume and application data go?</strong></summary>

Nowhere. Your data remains on your computer in your local `profile.yaml` and your local SQLite database (`careerforge.db`). CareerForge has no cloud backend, no account database, and no telemetry.
</details>

<details>
<summary><strong>Can I use CareerForge without Microsoft Word?</strong></summary>

Yes. CareerForge fully supports LibreOffice on Windows, macOS, and Linux. If Microsoft Word is installed on Windows, CareerForge uses it as a fast-path engine; otherwise, it falls back to LibreOffice automatically.
</details>

<details>
<summary><strong>Does CareerForge work on Linux?</strong></summary>

Yes. CareerForge supports Linux via community testing. Install `libreoffice-writer` through your distribution's package manager (`sudo apt-get install -y libreoffice-writer`) to enable PDF rendering.
</details>

<details>
<summary><strong>Do I need an OpenAI API key, Claude, or ChatGPT to run CareerForge?</strong></summary>

No. CareerForge uses zero external LLM APIs. Matching, resume tailoring, ATS checking, and style auditing use deterministic algorithms, regular expressions, and local computational linguistics heuristics on your CPU.
</details>

<details>
<summary><strong>Does CareerForge automatically submit applications for me?</strong></summary>

No. This is an intentional design choice. Mass automated submission bots often introduce errors, produce mismatched submissions, and trigger portal spam blocks. CareerForge prepares clean resumes and tracks your pipeline, but you retain full control over where and when you apply.
</details>

<details>
<summary><strong>What features assist remote job seekers from Bangladesh or the Global South?</strong></summary>

The `forge eligibility --my-country <CODE>` flag scans job descriptions for hidden geographical limits, US residency clauses, and timezone constraints. This helps international applicants identify roles that truly hire worldwide before spending time tailoring applications.
</details>

<details>
<summary><strong>How can I add a custom job board scraper or Anti-AI rule?</strong></summary>

Scrapers extend our base scraper interface documented in [docs/ADDING_A_SCRAPER.md](docs/ADDING_A_SCRAPER.md). Anti-AI rules are stored in a modular YAML configuration file located at `careerforge/data/anti_ai_rules.yaml`. You can submit new rules through pull requests.
</details>

---

## Roadmap and Status

CareerForge v0.5.0 includes all core workflow stages: scrapers, knapsack CV tailoring, ATS fragility simulation, SQLite tracking, funnel analytics, and interview story drafting.

Remaining items planned for upcoming releases:

- [ ] **Workable & SmartRecruiters Scrapers:** Add public posting scrapers for Workable and SmartRecruiters portals.
- [ ] **PyPI Publishing:** Publish official wheel and source packages to PyPI for standard `pipx install careerforge` distribution.
- [ ] **Docker Container:** Provide a pre-configured container image with headless LibreOffice for identical cross-platform rendering.
- [ ] **MkDocs Documentation Site:** Deploy searchable online documentation using MkDocs Material.
- [ ] **Community Translations:** Internationalize documentation and rule descriptions across community languages.
- [ ] **CLI Modularization:** Split `careerforge/cli.py` into dedicated sub-command modules.
- [ ] **Additional CV Templates:** Add modular LaTeX and HTML/CSS single-page ATS templates.

---

## Contributing

We welcome community contributions, bug reports, and rule improvements.

* **Good First Issues:** Check our [GitHub Issues](https://github.com/rafijurrahman/careerforge/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) labeled `good first issue`.
* **Adding a Scraper:** Read our step-by-step guide in [docs/ADDING_A_SCRAPER.md](docs/ADDING_A_SCRAPER.md).
* **Adding an Anti-AI Rule:** Edit `careerforge/data/anti_ai_rules.yaml` and submit a PR with test coverage.
* **Contribution Guidelines:** Review [CONTRIBUTING.md](CONTRIBUTING.md) for code style, git conventions, and branch management.
* **Code of Conduct:** CareerForge follows the Contributor Covenant standards outlined in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
* **Security Reporting:** Review our vulnerability reporting protocol in [SECURITY.md](SECURITY.md).

---

## Documentation Index

| Guide | Description |
| :--- | :--- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture, data models, and component boundaries. |
| [docs/ATS_SIM.md](docs/ATS_SIM.md) | Specification of the 13 diagnostic ATS fragility checks and scoring. |
| [docs/PRIVACY_MODEL.md](docs/PRIVACY_MODEL.md) | Threat model, network activity audit, and offline verification guide. |
| [docs/RESEARCH.md](docs/RESEARCH.md) | Computational linguistics papers and citations behind Anti-AI auditing. |
| [docs/ADDING_A_SCRAPER.md](docs/ADDING_A_SCRAPER.md) | How to write and register a new public job board scraper. |
| [docs/anti_ai_standards.md](docs/anti_ai_standards.md) | Editorial rules for human-voice writing and phrase replacement guide. |
| [docs/ELIGIBILITY.md](docs/ELIGIBILITY.md) | Heuristic rules for remote geographical and visa restriction analysis. |
| [docs/TRACK.md](docs/TRACK.md) | SQLite schema, event logging, and terminal Kanban usage. |
| [docs/INTERVIEW.md](docs/INTERVIEW.md) | STAR outline drafting and behavioral interview question banks. |
| [docs/COVER.md](docs/COVER.md) | Outreach templates, fill marker standards, and style validation. |
| [docs/SALARY.md](docs/SALARY.md) | Compensation parsing, percentile calculation, and exchange rate rules. |
| [docs/GHOST.md](docs/GHOST.md) | Ghost Job score calculation, posting age metrics, and repost detection. |

---

## License, Acknowledgments & Support

### License
CareerForge is licensed under the [MIT License](LICENSE).

### Open Source Dependencies
CareerForge relies on the following open-source libraries:
* **Document Processing:** `python-docx`, `pypdf`, `pdfminer.six`
* **CLI & Terminal Interface:** `rich`, `textual`
* **Configuration & Storage:** `pyyaml`, `platformdirs`, `pydantic`
* **HTTP Client:** `requests`

### Support
If CareerForge saves you time or helps your job search, star the repository on GitHub and share it with peers.
