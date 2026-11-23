"""
remotive_scanner.py
Scans Remotive public API for remote job listings.
API: https://remotive.com/api/remote-jobs?category={category}&limit={n}
No authentication required.
"""

import requests
from typing import List, Dict

# Remotive category slugs mapped to common role keywords
CATEGORY_MAP = {
    "data":               ["data analyst", "data scientist", "bi analyst", "analytics"],
    "software-dev":       ["developer", "engineer", "backend", "frontend", "fullstack"],
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
    """Map role keyword list to relevant Remotive category slugs."""
    matched = set()
    lower_keywords = [k.lower() for k in role_keywords]
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if any(kw in role.lower() for role in lower_keywords):
                matched.add(category)
    return list(matched) if matched else ["data"]  # fallback to data


def scan_remotive(
    target_roles: List[str],
    limit: int = 20,
    work_modes: List[str] = None,
) -> List[Dict]:
    """
    Fetch remote jobs from Remotive API.

    Args:
        target_roles: List of job title keywords (e.g. ["Data Analyst", "BI Analyst"])
        limit: Max results per category request
        work_modes: Unused for Remotive (all jobs are remote by definition)

    Returns:
        List of job dicts with keys: title, company, url, tags, published_at, location
    """
    categories = _role_to_categories(target_roles)
    results = []
    seen_ids = set()

    for category in categories:
        try:
            resp = requests.get(
                REMOTIVE_API,
                params={"category": category, "limit": limit},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])

            for job in jobs:
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                title = job.get("title", "")
                # Filter: check if job title matches any target role keyword
                match = any(
                    role.lower() in title.lower() for role in target_roles
                )
                if not match:
                    continue

                results.append({
                    "title":        title,
                    "company":      job.get("company_name", ""),
                    "url":          job.get("url", ""),
                    "tags":         ", ".join(job.get("tags", [])),
                    "published_at": job.get("publication_date", ""),
                    "location":     job.get("candidate_required_location", "Worldwide"),
                    "source":       "Remotive",
                })

        except requests.RequestException as exc:
            print(f"[remotive] Error fetching category '{category}': {exc}")

    return results


if __name__ == "__main__":
    # Quick test
    jobs = scan_remotive(["Data Analyst", "BI Analyst"], limit=5)
    print(f"\nRemotive — found {len(jobs)} matching jobs\n")
    for j in jobs:
        print(f"  [{j['company']}] {j['title']}")
        print(f"  {j['url']}")
        print(f"  Location: {j['location']} | Published: {j['published_at']}")
        print()
