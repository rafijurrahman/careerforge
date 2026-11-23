"""
work_mode_config.py
Reads preferred work modes from profile.yaml and applies location filters
to job search queries.

Default: Remote / Worldwide only.
User can extend in profile.yaml:

    target_preferences:
      preferred_work_modes:
        - Remote
        - Hybrid
        - On-site
"""

from typing import List

# Default when nothing is set in profile
DEFAULT_MODES = ["Remote"]

# Location keywords mapped per mode
MODE_FILTER_KEYWORDS = {
    "Remote":  ["remote", "worldwide", "anywhere", "global", "work from home", "wfh"],
    "Hybrid":  ["hybrid"],
    "On-site": ["on-site", "onsite", "office", "in-person", "in-office"],
}


def get_work_modes(profile: dict) -> List[str]:
    """
    Read preferred_work_modes from profile dict.
    Falls back to DEFAULT_MODES if not configured.
    """
    prefs = profile.get("target_preferences", {})
    modes = prefs.get("preferred_work_modes", DEFAULT_MODES)
    return [m.strip() for m in modes if isinstance(m, str)]


def location_matches(location_text: str, work_modes: List[str]) -> bool:
    """
    Check whether a job's location string matches the user's preferred work modes.

    Args:
        location_text: Raw location string from a job listing
        work_modes:    List of preferred modes (e.g. ["Remote", "Hybrid"])

    Returns:
        True if the job location fits at least one preferred mode.
    """
    if not location_text:
        # No location info — accept only if Remote is in modes
        return "Remote" in work_modes

    loc_lower = location_text.lower()

    for mode in work_modes:
        keywords = MODE_FILTER_KEYWORDS.get(mode, [])
        if any(kw in loc_lower for kw in keywords):
            return True

    return False


def filter_jobs_by_mode(jobs: List[dict], work_modes: List[str]) -> List[dict]:
    """
    Filter a list of job dicts to only those matching preferred work modes.

    Each job dict must have a 'location' key.
    """
    return [j for j in jobs if location_matches(j.get("location", ""), work_modes)]


def describe_modes(work_modes: List[str]) -> str:
    """Human-readable summary of active work modes."""
    return " + ".join(work_modes) if work_modes else "Remote"
