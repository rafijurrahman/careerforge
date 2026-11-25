"""
Greenhouse ATS Scraper Plugin for CareerForge.
Queries public Greenhouse board APIs and yields standardized JobPosting instances.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import requests

try:
    from careerforge.scrapers.base import BaseScraper, JobPosting, compute_dedup_hash
    from careerforge.scrapers.board_registry import GREENHOUSE_BOARDS
except ImportError:
    from scrapers.base import BaseScraper, JobPosting, compute_dedup_hash
    from scrapers.board_registry import GREENHOUSE_BOARDS

SENIOR_TERMS = ["senior", "lead", "principal", "manager", "director", "head of", "vp", "staff"]


class GreenhouseScraper(BaseScraper):
    name = "greenhouse"
    rate_limit_per_sec = 5.0

    def __init__(self, session: Optional[requests.Session] = None, boards: Optional[List[str]] = None):
        super().__init__(session=session)
        self.boards = boards or GREENHOUSE_BOARDS

    def _scan_board_with_status(
        self,
        board: str,
        keywords: List[str],
        exclude_senior: bool,
    ) -> Tuple[bool, str, List[JobPosting], Set[str]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        company_name = board.capitalize()
        results: List[JobPosting] = []
        live_ids: Set[str] = set()
        try:
            self._throttle()
            resp = self.session.get(url, timeout=6)
            if resp.status_code != 200:
                return False, company_name, results, live_ids

            data = resp.json()
            for idx, j in enumerate(data.get("jobs", [])):
                title = j.get("title", "")
                loc = j.get("location", {}).get("name", "Remote")
                job_id = str(j.get("id", f"{board}-{idx}"))
                ext_id = f"gh-{board}-{job_id}"
                live_ids.add(ext_id)
                live_ids.add(compute_dedup_hash(company_name, title, loc))

                t_low = title.lower()
                if any(k.lower() in t_low for k in keywords):
                    if exclude_senior and any(s in t_low for s in SENIOR_TERMS):
                        continue

                    results.append(
                        JobPosting(
                            id=ext_id,
                            title=title,
                            company=company_name,
                            location=loc,
                            remote_policy="Remote" if "remote" in loc.lower() or "worldwide" in loc.lower() else "On-site/Hybrid",
                            description=j.get("content"),
                            posted_at=j.get("updated_at"),
                            source_url=j.get("absolute_url", ""),
                            source="Greenhouse",
                        )
                    )
            return True, company_name, results, live_ids
        except Exception:
            return False, company_name, results, set()

    def _scan_board(self, board: str, keywords: List[str], exclude_senior: bool) -> List[JobPosting]:
        _, _, results, _ = self._scan_board_with_status(board, keywords, exclude_senior)
        return results

    def fetch_with_status(
        self,
        config: Dict[str, Any],
    ) -> Tuple[List[JobPosting], Dict[Tuple[str, str], Set[str]], List[Tuple[str, str]]]:
        """Executes board scans and also returns succeeded/failed company tracking."""
        keywords = config.get("keywords", ["Software Engineer"])
        exclude_senior = config.get("exclude_senior", True)
        boards = config.get("boards", self.boards)
        max_workers = config.get("max_workers", 10)

        postings: List[JobPosting] = []
        succeeded_boards: Dict[Tuple[str, str], Set[str]] = {}
        failed_boards: List[Tuple[str, str]] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._scan_board_with_status, b, keywords, exclude_senior)
                for b in boards
            ]
            for b, f in zip(boards, futures):
                try:
                    ok, company_name, items, live_ids = f.result()
                    if ok:
                        succeeded_boards[("Greenhouse", company_name)] = live_ids
                        postings.extend(items)
                    else:
                        failed_boards.append(("Greenhouse", company_name))
                except Exception:
                    failed_boards.append(("Greenhouse", b.capitalize()))
        return postings, succeeded_boards, failed_boards

    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        postings, _, _ = self.fetch_with_status(config)
        for item in postings:
            yield item

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
