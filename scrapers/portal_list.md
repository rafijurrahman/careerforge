# CareerForge — Free Job Portal Directory

**Default mode: 100% Remote / Worldwide only.**
To add Hybrid or On-site, edit your `profile.yaml`:

```yaml
target_preferences:
  preferred_work_modes:
    - Remote       # always keep this
    - Hybrid       # add if you want hybrid
    - On-site      # add if you want on-site
```

---

## 🌐 Dedicated Remote Job Boards (Free)

| Portal | URL | Best For | CareerForge Scanner |
|--------|-----|----------|---------------------|
| **Remotive** | [remotive.com](https://remotive.com) | Tech, Data, Marketing | ✅ `remotive_scanner.py` |
| **We Work Remotely** | [weworkremotely.com](https://weworkremotely.com) | Dev, Design, Data | Manual (no public API) |
| **Remote OK** | [remoteok.com](https://remoteok.com) | Dev, Data, Ops | Manual |
| **Jobicy** | [jobicy.com](https://jobicy.com) | APAC-friendly, global | Manual |
| **Working Nomads** | [workingnomads.com](https://workingnomads.com) | Dev, Analytics | Manual |
| **Daily Remote** | [dailyremote.com](https://dailyremote.com) | General remote | Manual |
| **Himalayas** | [himalayas.app](https://himalayas.app) | Tech, Data | Manual |
| **4 Day Week** | [4dayweek.io](https://4dayweek.io) | Work-life balance roles | Manual |
| **Jobspresso** | [jobspresso.co](https://jobspresso.co) | Tech, Marketing | Manual |
| **Career Vault** | [careervault.io](https://careervault.io) | Aggregated remote | Manual |
| **Remote.co** | [remote.co](https://remote.co) | Curated remote | Manual |

---

## 🏢 ATS Direct Boards (Free Public APIs)

These company ATS boards are publicly accessible. CareerForge scans them automatically.

| ATS Platform | Base URL | CareerForge Scanner |
|---|---|---|
| **Greenhouse** | `boards.greenhouse.io/{company}/jobs` | ✅ `greenhouse_scanner.py` |
| **Ashby** | `jobs.ashbyhq.com/{company}` | ✅ `ashby_scanner.py` |
| **Lever** | `jobs.lever.co/{company}` | 🔜 Planned |
| **Workable** | `apply.workable.com/{company}` | 🔜 Planned |

> Add your own company slugs in `scrapers/board_registry.py` under `GREENHOUSE_BOARDS` or `ASHBY_BOARDS`.

---

## 🚀 Startup & Founder-Direct (Free)

| Portal | URL | Notes |
|--------|-----|-------|
| **Wellfound (AngelList)** | [wellfound.com/jobs](https://wellfound.com/jobs) | Startup equity roles |
| **Y Combinator** | [workatastartup.com](https://www.workatastartup.com) | YC-backed startups |
| **Hacker News "Who is Hiring?"** | [whoishiring.me](https://whoishiring.me) | Monthly founder posts |
| **Welcome to the Jungle** | [welcometothejungle.com](https://welcometothejungle.com) | Europe-heavy, global remote |
| **Arc.dev** | [arc.dev](https://arc.dev) | Vetted remote developers |
| **Braintrust** | [app.usebraintrust.com](https://app.usebraintrust.com) | Talent-owned freelance network |

---

## 💼 Multi-Purpose Boards (Free Tier)

| Portal | URL | Filter to Use |
|--------|-----|---------------|
| **LinkedIn Jobs** | [linkedin.com/jobs](https://linkedin.com/jobs) | Filter: Remote + Past Week |
| **Indeed** | [indeed.com](https://indeed.com) | Filter: Remote |
| **Glassdoor** | [glassdoor.com](https://glassdoor.com) | Filter: Remote |

---

## 🤝 Contract & Freelance (Free)

| Portal | URL | Best For |
|--------|-----|----------|
| **Contra** | [contra.com](https://contra.com) | Independent contracts |
| **Hubstaff Talent** | [talent.hubstaff.com](https://talent.hubstaff.com) | Global contractor network |
| **Upwork** | [upwork.com](https://upwork.com) | Freelance projects |
| **Andela** | [andela.com](https://andela.com) | Senior remote talent |

---

## 🗣️ Community Boards (Free)

| Community | URL | Cadence |
|-----------|-----|---------|
| **Reddit r/forhire** | [reddit.com/r/forhire](https://reddit.com/r/forhire) | Daily |
| **Reddit r/RemoteJobs** | [reddit.com/r/remotejobs](https://reddit.com/r/remotejobs) | Daily |
| **Reddit r/hiring** | [reddit.com/r/hiring](https://reddit.com/r/hiring) | Daily |
| **Reddit r/freelance_forhire** | [reddit.com/r/freelance_forhire](https://reddit.com/r/freelance_forhire) | Daily |

---

## 📋 How to Use This List

1. **Automated scan** — run `python cli.py scrape --roles "Data Analyst" --limit 10`
   CareerForge hits Greenhouse + Ashby + Remotive simultaneously.

2. **Manual search** — open any portal above, paste your target role, set location to **Worldwide** or **Remote**.

3. **Switch from Remote to Hybrid** — edit `profile.yaml`:
   ```yaml
   target_preferences:
     preferred_work_modes:
       - Remote
       - Hybrid
   ```
   Then re-run `python cli.py scrape`.

---

> **Note:** Portals marked `Manual` do not have public APIs. CareerForge cannot auto-scrape them. Use them directly in your browser while running CareerForge for CV tailoring and application tracking.
