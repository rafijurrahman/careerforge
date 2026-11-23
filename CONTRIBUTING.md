# Contributing to CareerForge

Thanks for taking the time to contribute.

---

## Ways to Contribute

- Add a new job portal scanner (see below)
- Improve the CV builder templates
- Extend the Anti-AI audit engine with new patterns
- Fix bugs or improve error handling
- Improve documentation

---

## Adding a New Job Portal Scanner

CareerForge scanners live in `scrapers/`. Each scanner is a standalone Python file that returns a list of job dicts.

### Standard Job Dict Format

Every scanner must return a list where each item has these keys:

```python
{
    "title":    "Data Analyst",
    "company":  "Acme Corp",
    "url":      "https://jobs.example.com/apply/123",
    "location": "Remote / Worldwide",
    "source":   "MyPortal",         # or use "platform" key
}
```

Optional keys: `tags`, `published_at`, `description_snippet`

### Minimum Scanner Template

```python
# scrapers/myportal_scanner.py

import requests
from typing import List, Dict

API_URL = "https://api.myportal.com/jobs"

def scan_myportal(target_roles: List[str], limit: int = 20) -> List[Dict]:
    results = []
    try:
        resp = requests.get(API_URL, params={"limit": limit}, timeout=10)
        resp.raise_for_status()
        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            if any(role.lower() in title.lower() for role in target_roles):
                results.append({
                    "title":    title,
                    "company":  job.get("company", ""),
                    "url":      job.get("url", ""),
                    "location": job.get("location", "Remote"),
                    "source":   "MyPortal",
                })
    except requests.RequestException as e:
        print(f"[myportal] Error: {e}")
    return results
```

### Wire It Into the CLI

In `cli.py`, import your scanner and call it inside `cmd_scrape`:

```python
from scrapers.myportal_scanner import scan_myportal

# inside cmd_scrape:
myportal_matches = scan_myportal(target_roles=keywords, limit=args.limit)
all_matches = gh_matches + ashby_matches + rem_matches + myportal_matches
```

### Add It to the Portal List

Update `scrapers/portal_list.md` with the portal name, URL, and scanner status.

---

## Code Style

- Python 3.9+ compatible
- Type hints where practical
- Docstrings for all public functions
- No external dependencies beyond what is in `requirements.txt` unless necessary

---

## Submitting a Pull Request

1. Fork the repository
2. Create a branch: `git checkout -b add-lever-scanner`
3. Make your changes
4. Test locally: `python cli.py scrape --roles "Engineer" --limit 5`
5. Open a pull request with a clear description of what you added

---

## Reporting Issues

Open a GitHub Issue with:
- Python version (`python --version`)
- Operating system
- Command you ran
- Full error output
