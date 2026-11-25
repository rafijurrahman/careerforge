"""
Lever ATS Scraper Plugin for CareerForge.
Queries public Lever postings API (https://api.lever.co/v0/postings/{company}?mode=json).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import requests

try:
    from careerforge.scrapers.base import BaseScraper, JobPosting, compute_dedup_hash
    from careerforge.scrapers.board_registry import LEVER_BOARDS
except ImportError:
    from scrapers.base import BaseScraper, JobPosting, compute_dedup_hash
    from scrapers.board_registry import LEVER_BOARDS

SENIOR_TERMS = ["senior", "lead", "principal", "manager", "director", "head of", "vp", "staff"]


def _epoch_ms_to_iso(created_at: Any) -> Optional[str]:
    if not isinstance(created_at, (int, float)) or created_at <= 0:
        return None
    try:
        dt = datetime.fromtimestamp(float(created_at) / 1000.0, tz=timezone.utc)
        return dt.isoformat(timespec="seconds")
    except (ValueError, OSError):
        return None


class LeverScraper(BaseScraper):
    name = "lever"
    rate_limit_per_sec = 3.0

    def __init__(self, session: Optional[requests.Session] = None, boards: Optional[List[str]] = None):
        super().__init__(session=session)
        self.boards = boards or LEVER_BOARDS

    def _scan_board_with_status(
        self,
        board: str,
        keywords: List[str],
        exclude_senior: bool,
    ) -> Tuple[bool, str, List[JobPosting], Set[str]]:
        url = f"https://api.lever.co/v0/postings/{board}?mode=json"
        company_name = board.capitalize()
        results: List[JobPosting] = []
        live_ids: Set[str] = set()
        try:
            self._throttle()
            resp = self.session.get(url, timeout=8)
            if resp.status_code != 200:
                return False, company_name, results, live_ids

            jobs_list = resp.json()
            if not isinstance(jobs_list, list):
                return False, company_name, results, live_ids

            for idx, j in enumerate(jobs_list):
                title = j.get("text", "")
                categories = j.get("categories", {}) or {}
                loc = categories.get("location", "Remote") or "Remote"
                workplace = str(j.get("workplaceType", "")).lower()
                raw_id = str(j.get("id", f"{board}-{idx}"))
                ext_id = f"lever-{board}-{raw_id}"

                live_ids.add(ext_id)
                live_ids.add(compute_dedup_hash(company_name, title, loc))

                t_low = title.lower()
                if any(k.lower() in t_low for k in keywords):
                    if exclude_senior and any(s in t_low for s in SENIOR_TERMS):
                        continue

                    is_remote = (
                        workplace == "remote"
                        or "remote" in loc.lower()
                        or "worldwide" in loc.lower()
                    )
                    sal_range = j.get("salaryRange") or {}
                    sal_min = sal_range.get("min") if isinstance(sal_range, dict) else None
                    sal_max = sal_range.get("max") if isinstance(sal_range, dict) else None
                    sal_curr = sal_range.get("currency") if isinstance(sal_range, dict) else None

                    desc = j.get("descriptionPlain") or j.get("descriptionBodyPlain") or ""
                    results.append(
                        JobPosting(
                            id=ext_id,
                            title=title,
                            company=company_name,
                            location=loc,
                            remote_policy="Remote" if is_remote else "On-site/Hybrid",
                            salary_min=float(sal_min) if sal_min is not None else None,
                            salary_max=float(sal_max) if sal_max is not None else None,
                            currency=sal_curr,
                            description=desc,
                            posted_at=_epoch_ms_to_iso(j.get("createdAt")),
                            source_url=j.get("hostedUrl", f"https://jobs.lever.co/{board}"),
                            source="Lever",
                        )
                    )
            return True, company_name, results, live_ids
        except Exception:
            return False, company_name, results, set()

    def fetch_with_status(
        self,
        config: Dict[str, Any],
    ) -> Tuple[List[JobPosting], Dict[Tuple[str, str], Set[str]], List[Tuple[str, str]]]:
        keywords = config.get("keywords", ["Data Analyst", "Software Engineer"])
        exclude_senior = config.get("exclude_senior", True)
        boards = config.get("boards", self.boards)
        max_workers = config.get("max_workers", 8)

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
                        succeeded_boards[("Lever", company_name)] = live_ids
                        postings.extend(items)
                    else:
                        failed_boards.append(("Lever", company_name))
                except Exception:
                    failed_boards.append(("Lever", b.capitalize()))
        return postings, succeeded_boards, failed_boards

    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        postings, _, _ = self.fetch_with_status(config)
        for item in postings:
            yield item

    def healthcheck(self) -> bool:
        try:
            resp = self.session.get("https://api.lever.co/v0/postings/kinsta?mode=json", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def scan_all_lever(keywords: list, max_workers: int = 8, exclude_senior: bool = True) -> list:
    """Backward-compatible helper returning legacy job dictionaries."""
    scraper = LeverScraper()
    postings = scraper.fetch(
        {
            "keywords": keywords,
            "max_workers": max_workers,
            "exclude_senior": exclude_senior,
        }
    )
    return [
        {
            "platform": p.source,
            "company": p.company,
            "title": p.title,
            "location": p.location,
            "url": p.source_url,
            "description": p.description or "",
        }
        for p in postings
    ]
