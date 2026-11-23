# Adding a New Job Scraper to CareerForge

CareerForge uses an extensible plugin architecture for job board scanners. Anyone can add support for a new ATS or public job board by writing a single Python class that inherits from `BaseScraper`.

---

## 🏗️ Architecture Overview

All scrapers inherit from `careerforge.scrapers.base.BaseScraper` and yield standardized `JobPosting` Pydantic models.

```
BaseScraper (ABC)
   ├── GreenhouseScraper
   ├── AshbyScraper
   ├── RemotiveScraper
   └── YourNewScraper (e.g. LeverScraper)
```

### `JobPosting` Schema
Every scraper must yield instances of `JobPosting`:
```python
class JobPosting(BaseModel):
    id: str               # e.g. "lever-stripe-10492"
    title: str            # e.g. "Data Platform Engineer"
    company: str          # e.g. "Stripe"
    location: str         # e.g. "Remote (Worldwide)"
    remote_policy: str    # "Remote" or "On-site/Hybrid"
    source_url: str       # direct application link
    source: str           # "Lever"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None
    posted_at: Optional[str] = None
```

---

## 🛠️ Step-by-Step Tutorial: Adding a Lever Scraper

Here is a complete, working example implementing a scraper for companies hosted on Lever (`jobs.lever.co/{company}`).

### 1. Create the Scraper File
Save this as `careerforge/scrapers/lever_scanner.py`:

```python
"""
Lever ATS Scraper Plugin for CareerForge.
Queries public Lever API endpoints (https://api.lever.co/v0/postings/{company}).
"""

from typing import Iterator, List, Dict, Any, Optional
import requests
from careerforge.scrapers.base import BaseScraper, JobPosting

# Example Lever company slugs
LEVER_BOARDS = [
    "automattic",
    "gitbook",
    "kinsta",
    "hotjar",
]

SENIOR_TERMS = ["senior", "lead", "principal", "manager", "director", "head of", "vp"]


class LeverScraper(BaseScraper):
    name = "lever"
    rate_limit_per_sec = 3.0  # Polite throttling

    def __init__(self, session: Optional[requests.Session] = None, boards: Optional[List[str]] = None):
        super().__init__(session=session)
        self.boards = boards or LEVER_BOARDS

    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        keywords = config.get("keywords", ["Data Analyst", "Software Engineer"])
        exclude_senior = config.get("exclude_senior", True)

        for board in self.boards:
            url = f"https://api.lever.co/v0/postings/{board}?mode=json"
            try:
                self._throttle()
                resp = self.session.get(url, timeout=8)
                if resp.status_code != 200:
                    continue

                for job in resp.json():
                    title = job.get("text", "")
                    t_lower = title.lower()

                    # Keyword match check
                    if not any(k.lower() in t_lower for k in keywords):
                        continue

                    # Filter senior titles if requested
                    if exclude_senior and any(s in t_lower for s in SENIOR_TERMS):
                        continue

                    categories = job.get("categories", {})
                    location = categories.get("location", "Remote")
                    commitment = categories.get("commitment", "Full-time")

                    yield JobPosting(
                        id=f"lever-{board}-{job.get('id', '')}",
                        title=title,
                        company=board.capitalize(),
                        location=location,
                        remote_policy="Remote" if "remote" in location.lower() else "On-site",
                        source_url=job.get("hostedUrl", f"https://jobs.lever.co/{board}"),
                        source="Lever",
                    )
            except Exception:
                continue

    def healthcheck(self) -> bool:
        try:
            resp = self.session.get("https://api.lever.co/v0/postings/automattic?mode=json", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
```

### 2. Write Contract Test with Mock Fixture
Create `tests/fixtures/lever_sample.json`:
```json
[
  {
    "id": "lever-sample-01",
    "text": "Data Analyst (Remote)",
    "hostedUrl": "https://jobs.lever.co/automattic/lever-sample-01",
    "categories": {
      "location": "Worldwide - Remote",
      "commitment": "Full-time"
    }
  }
]
```

Add offline test in `tests/test_scrapers.py`:
```python
def test_lever_scraper_offline_fixture():
    fixture_data = load_fixture("lever_sample.json")
    mock_session = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fixture_data
    mock_session.get.return_value = mock_resp

    scraper = LeverScraper(session=mock_session, boards=["automattic"])
    postings = list(scraper.fetch({"keywords": ["Data Analyst"]}))

    assert len(postings) == 1
    assert postings[0].source == "Lever"
    assert postings[0].company == "Automattic"
```

### 3. Open a Pull Request
1. Branch off main: `git checkout -b add-lever-scraper`
2. Run tests: `pytest -v`
3. Submit a PR using the `.github/PULL_REQUEST_TEMPLATE.md`.
