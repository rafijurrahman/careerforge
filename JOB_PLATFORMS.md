# Curated Directory of Free Job Search Platforms

> **Default CareerForge Search Mode:** 100% Remote / Worldwide only.  
> You can switch or expand your mode to **Hybrid** or **On-site** anytime in your `profile.yaml`.

---

## 📌 Table of Contents
1. [Dedicated Global Remote Job Boards](#1-dedicated-global-remote-job-boards)
2. [Direct Employer ATS & Search Dorks](#2-direct-employer-ats--search-dorks)
3. [Startup & Founder-Direct Portals](#3-startup--founder-direct-portals)
4. [Vetting & Contract Platforms](#4-vetting--contract-platforms)
5. [Freelance & Project Marketplaces](#5-freelance--project-marketplaces)
6. [Tech Communities & Monthly Hiring Boards](#6-tech-communities--monthly-hiring-boards)
7. [How to Switch from Remote to Hybrid / On-site](#7-how-to-switch-from-remote-to-hybrid--on-site)

---

## 1. Dedicated Global Remote Job Boards
All platforms below are 100% free to search and apply directly with employers.

| Platform | URL | Focus Areas | CareerForge Scanner |
|---|---|---|:---:|
| **Remotive** | [remotive.com](https://remotive.com) | Tech, Data, Operations, QA | ✅ Built-in (`remotive_scanner.py`) |
| **Himalayas** | [himalayas.app](https://himalayas.app) | Software, Analytics, Product, Operations | Manual |
| **We Work Remotely** | [weworkremotely.com](https://weworkremotely.com) | Engineering, Data, DevOps, Support | Manual |
| **Remote OK** | [remoteok.com](https://remoteok.com) | Tech, Data, Cloud, Marketing | Manual |
| **Jobicy** | [jobicy.com](https://jobicy.com) | APAC & Global Remote roles | Manual |
| **Working Nomads** | [workingnomads.com](https://workingnomads.com) | Curated Development, Data, Ops | Manual |
| **Daily Remote** | [dailyremote.com](https://dailyremote.com) | General Remote across disciplines | Manual |
| **4 Day Week** | [4dayweek.io](https://4dayweek.io) | Companies with 32h workweeks | Manual |
| **Jobspresso** | [jobspresso.co](https://jobspresso.co) | Hand-curated remote tech & operations | Manual |
| **Career Vault** | [careervault.io](https://careervault.io) | Aggregated non-stale remote listings | Manual |

---

## 2. Direct Employer ATS & Search Dorks
Instead of third-party middlemen, these scan company Applicant Tracking Systems directly.

| ATS System | Scanner / Search Method | Status in CareerForge |
|---|---|:---:|
| **Greenhouse** | `boards.greenhouse.io/{company}/jobs` | ✅ Built-in (`greenhouse_scanner.py`) |
| **Ashby** | `jobs.ashbyhq.com/{company}` | ✅ Built-in (`ashby_scanner.py`) |
| **Lever** | `jobs.lever.co/{company}` | 🔜 Planned |
| **Workable** | `apply.workable.com/{company}` | 🔜 Planned |

### Google Search Dorks (Find Hidden Unindexed Jobs)
Paste these search queries directly into Google to surface live job pages:
* **Greenhouse:** `site:boards.greenhouse.io ("Data Analyst" OR "Software Engineer") ("Worldwide" OR "Anywhere" OR "Remote")`
* **Ashby:** `site:jobs.ashbyhq.com ("Data Analyst" OR "Engineer") "Remote" ("Anywhere" OR "Global")`
* **Lever:** `site:jobs.lever.co ("Analyst" OR "Developer") ("Remote - Worldwide" OR "Work from Anywhere")`

---

## 3. Startup & Founder-Direct Portals
Skip HR gatekeepers and reach founding teams directly.

* **[Wellfound (formerly AngelList Talent)](https://wellfound.com/jobs)**  
  Direct messaging to founders, transparent equity and salary ranges, filterable by *Worldwide Remote*.
* **[Y Combinator (Work at a Startup)](https://www.workatastartup.com/)**  
  Single profile applies across hundreds of active YC companies hiring worldwide.
* **[Welcome to the Jungle (Otta)](https://welcome.ottajobs.com/)**  
  Curated high-signal startups with verified remote policies.
* **[Arc.dev](https://arc.dev)**  
  Vetted remote engineering and data roles with global hiring support.
* **[Braintrust](https://app.usebraintrust.com/)**  
  Talent-owned network with high-rate tech contracts.

---

## 4. Vetting & Contract Platforms
Verified remote evaluation, test engineering, and technical matching networks.

* **[Askable](https://www.askable.com/experts)** — AI evaluation, SQL/Python benchmarks, paid hourly/task.
* **[Turing](https://www.turing.com/jobs)** — Automated technical vetting matching international talent with US tech firms.
* **[Mercor](https://mercor.com/)** — AI-vetted video and resume placement for remote Silicon Valley startups.
* **[OneForma](https://www.oneforma.com/)** — Data evaluation, localization, and search quality rating.

---

## 5. Freelance & Project Marketplaces
No platform fees or direct contractor arrangements:

* **[Contra](https://contra.com/)** — Zero commission network for client management, contracts, and invoicing.
* **[Hubstaff Talent](https://talent.hubstaff.com/)** — Free marketplace for worldwide remote contractors.
* **[Upwork](https://www.upwork.com/)** — Direct client projects for SQL, Power BI, Python, and analytics automation.

---

## 6. Tech Communities & Monthly Hiring Boards

* **[Hacker News "Who is Hiring?"](https://whoishiring.me/)**  
  Posted on the 1st of every month on Y Combinator's Hacker News. Directly posted by engineering managers and founders. Filter by *Remote*.
* **Reddit Hiring Subreddits:**
  * `r/forhire` — Strictly moderated marketplace with mandatory wage disclosures ($15+/hr minimum).
  * `r/RemoteJobs` — Community leads and verified remote company hiring calls.
  * `r/jobbit` — Software, analytics, and database-focused roles.
  * `r/hiring` & `r/freelance_forhire` — Contract and direct employment postings.

---

## 7. How to Switch from Remote to Hybrid / On-site

By default, CareerForge prioritizes **100% Remote / Worldwide** positions so you don't waste time on country-restricted listings.

If you want to apply for local, hybrid, or on-site opportunities in your city:

1. Open your `profile.yaml`:
   ```yaml
   target_preferences:
     preferred_work_modes:
       - Remote
       - Hybrid       # Add this
       - On-site      # Add this
     preferred_locations:
       - "Worldwide"
       - "Dhaka, Bangladesh"  # Add your specific city or region
   ```
2. Re-run your search or CV generation:
   ```bash
   python cli.py scrape --roles "Data Analyst"
   python cli.py apply --role-tag "Dhaka_Hybrid"
   ```
CareerForge will immediately expand its search criteria and tailor your CV location header accordingly.
