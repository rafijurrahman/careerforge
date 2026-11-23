"""
Multi-Threaded Greenhouse Board Scanner.
Queries Greenhouse open APIs in real-time for any target role keywords.
"""

import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor
from scrapers.board_registry import GREENHOUSE_BOARDS

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scan_board(board: str, keywords: list, exclude_senior: bool = True) -> list:
    """Scans a single Greenhouse board for matching job postings."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    matches = []
    senior_terms = ["senior", "lead", "principal", "manager", "director", "head of", "vp"]

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            jobs = data.get("jobs", [])
            for j in jobs:
                title = j.get("title", "")
                t_low = title.lower()
                
                # Check keyword match
                if any(k.lower() in t_low for k in keywords):
                    if exclude_senior and any(s in t_low for s in senior_terms):
                        continue
                    
                    loc = j.get("location", {}).get("name", "Remote")
                    matches.append({
                        "platform": "Greenhouse",
                        "company": board.capitalize(),
                        "title": title,
                        "location": loc,
                        "url": j.get("absolute_url")
                    })
    except Exception:
        pass

    return matches

def scan_all_greenhouse(keywords: list, max_workers: int = 20, exclude_senior: bool = True) -> list:
    """Scans all registered Greenhouse company boards concurrently."""
    all_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scan_board, b, keywords, exclude_senior) for b in GREENHOUSE_BOARDS]
        for f in futures:
            res = f.result()
            if res:
                all_results.extend(res)
    return all_results
