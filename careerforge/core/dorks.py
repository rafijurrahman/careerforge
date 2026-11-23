"""
Google ATS Dork Generator for Direct-to-Employer Remote Job Discovery.
Generates targeted queries that bypass aggregators and find live listings on ATS domains.
"""

import urllib.parse
from typing import Dict, List


def generate_ats_dorks(role: str, location: str = "remote", extra_keywords: str = "") -> List[Dict[str, str]]:
    """
    Generates high-precision Google search queries for major ATS platforms:
    - Greenhouse (boards.greenhouse.io)
    - Lever (jobs.lever.co)
    - Ashby (jobs.ashbyhq.com)
    - Workable (apply.workable.com)
    - Hacker News (news.ycombinator.com)
    """
    clean_role = role.strip()
    loc_part = f'"{location}"' if location else ""
    extra_part = f'"{extra_keywords}"' if extra_keywords else ""

    platforms = [
        {
            "platform": "Greenhouse",
            "dork": f'site:boards.greenhouse.io "{clean_role}" {loc_part} {extra_part}'.strip(),
            "description": "Greenhouse-hosted direct job boards",
        },
        {
            "platform": "Lever",
            "dork": f'site:jobs.lever.co "{clean_role}" {loc_part} {extra_part}'.strip(),
            "description": "Lever-hosted global listings",
        },
        {
            "platform": "Ashby",
            "dork": f'site:jobs.ashbyhq.com "{clean_role}" {loc_part} {extra_part}'.strip(),
            "description": "Ashby high-growth startup listings",
        },
        {
            "platform": "Workable",
            "dork": f'site:apply.workable.com "{clean_role}" {loc_part} {extra_part}'.strip(),
            "description": "Workable employer portals",
        },
        {
            "platform": "Hacker News",
            "dork": f'site:news.ycombinator.com "Ask HN: Who is hiring?" "{clean_role}" {loc_part}'.strip(),
            "description": "Hacker News monthly founder hiring threads",
        },
    ]

    for p in platforms:
        encoded_query = urllib.parse.quote_plus(p["dork"])
        p["url"] = f"https://www.google.com/search?q={encoded_query}"

    return platforms
