"""
Remotive Scraper Plugin for CareerForge.
Scans Remotive public API for remote job listings and yields JobPosting instances.
"""

from typing import Any, Dict, Iterator, List

try:
    from careerforge.scrapers.base import BaseScraper, JobPosting
except ImportError:
    from scrapers.base import BaseScraper, JobPosting

CATEGORY_MAP = {
    "data":               ["data analyst", "data scientist", "bi analyst", "analytics", "sql"],
    "software-dev":       ["developer", "engineer", "backend", "frontend", "fullstack", "software"],
    "devops-sysadmin":    ["devops", "sysadmin", "cloud", "infrastructure"],
    "product":            ["product manager", "product owner", "pm"],
    "design":             ["designer", "ux", "ui", "graphic"],
    "marketing":          ["marketing", "seo", "content", "growth"],
    "finance-legal":      ["accountant", "finance", "legal", "compliance"],
    "hr":                 ["recruiter", "hr", "people ops", "talent"],
    "customer-support":   ["support", "customer success", "account manager"],
    "writing":            ["writer", "copywriter", "technical writer", "editor"],
    "project-mgmt":       ["project manager", "scrum master", "agile"],
    "qa":                 ["qa", "tester", "quality assurance"],
}

REMOTIVE_API = "https://remotive.com/api/remote-jobs"


def _role_to_categories(role_keywords: List[str]) -> List[str]:
    matched = set()
    lower_keywords = [k.lower() for k in role_keywords]
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if any(kw in role.lower() for role in lower_keywords):
                matched.add(category)
    return list(matched) if matched else ["data", "software-dev"]


class RemotiveScraper(BaseScraper):
    name = "remotive"
    rate_limit_per_sec = 2.0

    def fetch(self, config: Dict[str, Any]) -> Iterator[JobPosting]:
        target_roles = config.get("target_roles") or config.get("keywords") or ["Data Analyst"]
        limit = config.get("limit", 20)
        categories = _role_to_categories(target_roles)
        seen_ids = set()

        for category in categories:
            try:
                self._throttle()
                resp = self.session.get(
                    REMOTIVE_API,
                    params={"category": category, "limit": limit},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for job in data.get("jobs", []):
                        job_id = str(job.get("id"))
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        title = job.get("title", "")
                        match = any(role.lower() in title.lower() for role in target_roles)
                        if not match:
                            continue

                        yield JobPosting(
                            id=f"remotive-{job_id}",
                            title=title,
                            company=job.get("company_name", "Unknown"),
                            location=job.get("candidate_required_location", "Worldwide"),
                            remote_policy="Remote",
                            description=job.get("description"),
                            posted_at=job.get("publication_date"),
                            source_url=job.get("url", ""),
                            source="Remotive",
                        )
            except Exception:
                continue

    def healthcheck(self) -> bool:
        try:
            resp = self.session.get(REMOTIVE_API, params={"limit": 1}, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def scan_remotive(target_roles: List[str], limit: int = 20, work_modes: List[str] = None) -> List[Dict]:
    """Backward compatibility wrapper returning legacy dicts."""
    scraper = RemotiveScraper()
    postings = scraper.fetch({"target_roles": target_roles, "limit": limit})
    return [
        {
            "title": p.title,
            "company": p.company,
            "url": p.source_url,
            "tags": "",
            "published_at": p.posted_at or "",
            "location": p.location,
            "source": "Remotive",
        }
        for p in postings
    ]
