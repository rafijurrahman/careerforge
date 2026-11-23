"""
Greenhouse ATS Scraper Plugin for CareerForge.
Queries public Greenhouse board APIs and yields standardized JobPosting instances.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional

import requests

try:
    from careerforge.scrapers.base import BaseScraper, JobPosting
    from careerforge.scrapers.board_registry import GREENHOUSE_BOARDS
except ImportError:
    from scrapers.base import BaseScraper, JobPosting
    from scrapers.board_registry import GREENHOUSE_BOARDS

SENIOR_TERMS = ["senior", "lead", "principal", "manager", "director", "head of", "vp", "staff"]


class GreenhouseScraper(BaseScraper):
    name = "greenhouse"
    rate_limit_per_sec = 5.0

    def __init__(self, session: Optional[requests.Session] = None, boards: Optional[List[str]] = None):
        super().__init__(session=session)
        self.boards = boards or GREENHOUSE_BOARDS

    def _scan_board(self, board: str, keywords: List[str], exclude_senior: bool) -> List[JobPosting]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        results = []
        try:
            self._throttle()
            resp = self.session.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                for j in data.get("jobs", []):
                    title = j.get("title", "")
                    t_low = title.lower()

                    if any(k.lower() in t_low for k in keywords):
                        if exclude_senior and any(s in t_low for s in SENIOR_TERMS):
                            continue

                        loc = j.get("location", {}).get("name", "Remote")
                        job_id = str(j.get("id", f"{board}-{len(results)}"))
                        results.append(
                            JobPosting(
                                id=f"gh-{board}-{job_id}",
                                title=title,
                                company=board.capitalize(),
                                location=loc,
                                remote_policy="Remote" if "remote" in loc.lower() or "worldwide" in loc.lower() else "On-site/Hybrid",
                                posted_at=j.get("updated_at"),
                                source_url=j.get("absolute_url", ""),
                                source="Greenhouse",
                            )
                        )
        except Exception:
            pass
        return results

    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        keywords = config.get("keywords", ["Software Engineer"])
        exclude_senior = config.get("exclude_senior", True)
        boards = config.get("boards", self.boards)
        max_workers = config.get("max_workers", 10)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._scan_board, b, keywords, exclude_senior)
                for b in boards
            ]
            for f in futures:
                try:
                    items = f.result()
                    for item in items:
                        yield item
                except Exception:
                    continue

    def healthcheck(self) -> bool:
        try:
            resp = self.session.get("https://boards-api.greenhouse.io/v1/boards/canonical/jobs", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def scan_all_greenhouse(keywords: list, max_workers: int = 15, exclude_senior: bool = True) -> list:
    """Backward compatibility wrapper returning legacy dicts."""
    scraper = GreenhouseScraper()
    postings = scraper.fetch({
        "keywords": keywords,
        "max_workers": max_workers,
        "exclude_senior": exclude_senior,
    })
    return [
        {
            "platform": p.source,
            "company": p.company,
            "title": p.title,
            "location": p.location,
            "url": p.source_url,
        }
        for p in postings
    ]
