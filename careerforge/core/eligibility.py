"""
Heuristic Remote Geo-Eligibility Checker (`careerforge/core/eligibility.py`).
Inspects job descriptions for location, timezone, work-authorization, and visa
restrictions using verifiable patterns in careerforge/data/eligibility_rules.yaml.

Notice: Outputs heuristic guidance only; does not provide legal immigration advice.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources

HEURISTIC_NOTICE = "Heuristic eligibility estimate from text rules; always verify requirements in the original posting."

COUNTRY_ALIASES: Dict[str, str] = {
    "bd": "BD",
    "bangladesh": "BD",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "uk": "UK",
    "gb": "UK",
    "united kingdom": "UK",
    "ca": "CA",
    "canada": "CA",
    "de": "EU",
    "germany": "EU",
    "fr": "EU",
    "france": "EU",
    "nl": "EU",
    "netherlands": "EU",
    "es": "EU",
    "spain": "EU",
    "pl": "EU",
    "poland": "EU",
    "eu": "EU",
    "europe": "EU",
    "in": "IN",
    "india": "IN",
    "au": "AU",
    "australia": "AU",
    "br": "LATAM",
    "brazil": "LATAM",
    "mx": "LATAM",
    "mexico": "LATAM",
}

EU_MEMBERS = {"EU", "DE", "FR", "NL", "ES", "PL", "SE", "IE", "IT", "PT", "FI", "DK", "AT", "BE"}


def load_eligibility_rules() -> Tuple[List[Dict[str, Any]], List[str]]:
    """Loads rules and negative false-positive guards from eligibility_rules.yaml."""
    raw: Dict[str, Any] = {}
    try:
        ref = resources.files("careerforge.data").joinpath("eligibility_rules.yaml")
        with ref.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception:
        local_path = os.path.join(os.path.dirname(__file__), "..", "data", "eligibility_rules.yaml")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

    return raw.get("rules", []), raw.get("negative_guards", [])


def _normalize_country(country: Optional[str]) -> Optional[str]:
    if not country:
        return None
    clean = country.strip().lower()
    if clean in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[clean]
    return clean.upper()


def _infer_subregion_from_snippet(snippet: str, default_region: str) -> str:
    low = snippet.lower()
    if default_region != "REGIONAL":
        return default_region
    for token, code in (
        ("north america", "NA"),
        ("latin america", "LATAM"),
        ("latam", "LATAM"),
        ("emea", "EMEA"),
        ("apac", "APAC"),
        ("australia", "AU"),
        ("india", "IN"),
        ("germany", "EU"),
        ("singapore", "SG"),
        ("canada", "CA"),
        ("europe", "EU"),
        ("uk", "UK"),
        ("usa", "US"),
        ("us", "US"),
    ):
        if re.search(rf"\b{re.escape(token)}\b", low):
            return code
    return default_region


def _can_apply_verdict(
    status: str,
    regions: List[str],
    my_country: Optional[str],
) -> Optional[Dict[str, Any]]:
    norm_country = _normalize_country(my_country)
    if not norm_country:
        return None

    if status == "Eligible":
        return {
            "country": norm_country,
            "eligible": True,
            "verdict": f"Yes (heuristic: no restriction found for {norm_country})",
        }

    # Check if restriction matches the user's country directly
    restricted_only = [r for r in regions if r not in ("VISA_RESTRICTED", "AMERICAS_TZ")]
    if restricted_only:
        matches_country = False
        for r in restricted_only:
            if r == norm_country:
                matches_country = True
            elif r == "EU" and norm_country in EU_MEMBERS:
                matches_country = True
            elif r == "NA" and norm_country in ("US", "CA"):
                matches_country = True
            elif r == "EMEA" and norm_country in (EU_MEMBERS | {"UK"}):
                matches_country = True
        if matches_country:
            return {
                "country": norm_country,
                "eligible": True,
                "verdict": f"Likely Yes (heuristic: matches permitted region {', '.join(restricted_only)})",
            }
        return {
            "country": norm_country,
            "eligible": False,
            "verdict": f"No (heuristic: restricted to {', '.join(restricted_only)})",
        }

    # Visa or timezone warning
    return {
        "country": norm_country,
        "eligible": False,
        "verdict": f"Check JD (heuristic: {', '.join(regions)} constraint detected)",
    }


def check_eligibility(
    jd_text: str,
    my_country: Optional[str] = None,
    rules: Optional[List[Dict[str, Any]]] = None,
    negative_guards: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluates remote geo-eligibility heuristics on a job description.
    Restrictions explicitly override generic 'worldwide' claims.
    """
    if rules is None or negative_guards is None:
        loaded_rules, loaded_guards = load_eligibility_rules()
        if rules is None:
            rules = loaded_rules
        if negative_guards is None:
            negative_guards = loaded_guards

    text = jd_text or ""
    # Split into sentence-like segments so negative guards apply per sentence cleanly
    segments = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]

    evidence: List[Dict[str, str]] = []
    seen_pairs = set()

    for seg in segments:
        is_office_desc = any(re.search(g, seg, re.IGNORECASE) for g in negative_guards)
        has_mandatory_lang = bool(
            re.search(
                r"\b(?:must|required|only|authorized|citizens?|sponsorship|eligible|reside)\b",
                seg,
                re.IGNORECASE,
            )
        )
        if is_office_desc and not has_mandatory_lang:
            continue

        for rule in rules:
            pat = rule.get("regex", "")
            if not pat:
                continue
            m = re.search(pat, seg, re.IGNORECASE)
            if m:
                rule_id = rule.get("id", "ELIG-RULE")
                region = _infer_subregion_from_snippet(seg, rule.get("region", "REGIONAL"))
                pair_key = (rule_id, region, seg[:80])
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                evidence.append(
                    {
                        "rule_id": rule_id,
                        "region": region,
                        "severity": rule.get("severity", "likely_restricted"),
                        "snippet": seg[:180],
                        "notes": rule.get("notes", ""),
                    }
                )

    has_restricted = any(e["severity"] == "restricted" for e in evidence)
    has_likely = any(e["severity"] == "likely_restricted" for e in evidence)

    # Explicit restriction always takes precedence even when "worldwide" appears elsewhere
    if has_restricted:
        status = "Restricted"
    elif has_likely:
        status = "Likely restricted"
    else:
        status = "Eligible"

    regions = sorted({e["region"] for e in evidence})
    can_apply = _can_apply_verdict(status, regions, my_country)

    return {
        "status": status,
        "heuristic": True,
        "notice": HEURISTIC_NOTICE,
        "regions": regions,
        "evidence": evidence,
        "can_apply": can_apply,
    }
