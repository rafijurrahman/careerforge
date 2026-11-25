"""
Heuristic Salary Band Analyzer (`forge salary`).
Aggregates min/median/max/percentiles strictly from stored jobs with disclosed salaries.
Currency conversion uses ONLY user-provided --rates YAML files (no online/hardcoded rates,
no cost-of-living adjustments).
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    from careerforge.core.store import CareerStore
except ImportError:
    from core.store import CareerStore

HEURISTIC_NOTICE = (
    "Heuristic compensation estimate based strictly on stored job records (no cost-of-living adjustments)."
)
SELECTION_BIAS_WARNING = (
    "Selection-bias warning: calculated solely from postings that disclose salary ranges; "
    "employers omitting compensation are not represented."
)


class SalaryError(Exception):
    """Raised on invalid rates files or invalid salary parameters."""


def load_rates_file(rates_path: str, target_currency: Optional[str] = None) -> Tuple[str, Dict[str, float]]:
    """
    Loads user-supplied currency conversion rates from YAML.
    Supports:
      base: USD
      rates:
        USD: 1.0
        EUR: 1.1
    or a flat mapping `{USD: 1.0, EUR: 1.1}` when `--currency` specifies the target currency.
    Multiplier means `amount_in_currency * rate = amount_in_base`.
    """
    if not os.path.exists(rates_path):
        raise SalaryError(f"Rates file not found: '{rates_path}'")

    try:
        with open(rates_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        raise SalaryError(f"Failed to parse rates YAML '{rates_path}': {e}") from e

    if not isinstance(raw, dict) or not raw:
        raise SalaryError("Rates YAML must be a non-empty mapping.")

    if "rates" in raw and isinstance(raw["rates"], dict):
        base = str(target_currency or raw.get("base") or "USD").strip().upper()
        rate_map = raw["rates"]
    else:
        base = str(target_currency or "USD").strip().upper()
        rate_map = raw

    normalized: Dict[str, float] = {}
    for code, mult in rate_map.items():
        if code == "base":
            continue
        try:
            val = float(mult)
        except (TypeError, ValueError) as e:
            raise SalaryError(f"Invalid numeric multiplier for currency '{code}': {mult}") from e
        if val <= 0:
            raise SalaryError(f"Conversion multiplier for '{code}' must be > 0.")
        normalized[str(code).strip().upper()] = val

    normalized.setdefault(base, 1.0)
    return base, normalized


def compute_percentile(sorted_vals: List[float], pct: float) -> float:
    """Computes linear-interpolated percentile (0-100) without external dependencies."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return round(sorted_vals[0], 2)

    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(sorted_vals[int(k)], 2)
    val = sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)
    return round(val, 2)


def analyze_salaries(
    store: CareerStore,
    role: Optional[str] = None,
    keyword: Optional[str] = None,
    currency: Optional[str] = None,
    rates_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Aggregates min/p25/median/p75/max compensation statistics from jobs with disclosed salaries.
    """
    jobs = store.list_jobs(limit=None, include_closed=True)

    filter_terms: List[str] = []
    if role:
        filter_terms.append(role.strip().lower())
    if keyword:
        filter_terms.append(keyword.strip().lower())

    target_base: Optional[str] = None
    rate_map: Optional[Dict[str, float]] = None
    if rates_path:
        target_base, rate_map = load_rates_file(rates_path, target_currency=currency)

    grouped_midpoints: Dict[str, List[float]] = {}
    grouped_mins: Dict[str, List[float]] = {}
    grouped_maxs: Dict[str, List[float]] = {}
    skipped_currencies: Dict[str, int] = {}

    for j in jobs:
        s_min = j.get("salary_min")
        s_max = j.get("salary_max")
        if s_min is None and s_max is None:
            continue

        if filter_terms:
            haystack = f"{j.get('title', '')} {j.get('description', '')}".lower()
            if not all(term in haystack for term in filter_terms):
                continue

        raw_curr = str(j.get("currency") or "UNKNOWN").strip().upper()
        if currency and not rates_path and raw_curr != currency.strip().upper():
            continue

        low = float(s_min) if s_min is not None else float(s_max)  # type: ignore[arg-type]
        high = float(s_max) if s_max is not None else float(s_min)  # type: ignore[arg-type]
        if low > high:
            low, high = high, low
        mid = (low + high) / 2.0

        if rate_map is not None and target_base is not None:
            if raw_curr not in rate_map:
                skipped_currencies[raw_curr] = skipped_currencies.get(raw_curr, 0) + 1
                continue
            mult = rate_map[raw_curr]
            low = low * mult
            high = high * mult
            mid = mid * mult
            out_curr = target_base
        else:
            out_curr = raw_curr

        grouped_midpoints.setdefault(out_curr, []).append(mid)
        grouped_mins.setdefault(out_curr, []).append(low)
        grouped_maxs.setdefault(out_curr, []).append(high)

    buckets: List[Dict[str, Any]] = []
    total_count = 0
    for curr_code, mids in sorted(grouped_midpoints.items()):
        sorted_mids = sorted(mids)
        count = len(sorted_mids)
        total_count += count
        buckets.append(
            {
                "currency": curr_code,
                "count": count,
                "min": round(min(grouped_mins[curr_code]), 2),
                "p25": compute_percentile(sorted_mids, 25),
                "median": compute_percentile(sorted_mids, 50),
                "p75": compute_percentile(sorted_mids, 75),
                "max": round(max(grouped_maxs[curr_code]), 2),
                "sample_too_small": count < 10,
            }
        )

    warnings: List[str] = [SELECTION_BIAS_WARNING]
    if total_count == 0:
        warnings.append("No matching job records with disclosed salary fields found.")
    elif total_count < 10:
        warnings.append(
            f"Sample too small ({total_count} disclosed job(s) < 10): salary percentiles are rough estimates."
        )
    if skipped_currencies:
        skipped_desc = ", ".join(f"{k} ({v})" for k, v in sorted(skipped_currencies.items()))
        warnings.append(
            f"Skipped postings with unmapped currencies in --rates: {skipped_desc}."
        )

    return {
        "heuristic": True,
        "notice": HEURISTIC_NOTICE,
        "role_filter": role,
        "keyword_filter": keyword,
        "converted_with_rates": bool(rates_path),
        "total_disclosed": total_count,
        "sample_too_small": total_count < 10,
        "warnings": warnings,
        "buckets": buckets,
        "skipped_currencies": skipped_currencies,
    }
