"""
Anti-AI Linguistic Audit & Sanitization Engine.
Implements rules derived from computational linguistics research (PNAS, Science Advances, ACL).
Loads rules dynamically from careerforge/data/anti_ai_rules.yaml.
"""

import re
from typing import Any, Dict, List, Optional

import yaml

try:
    from importlib import resources
except ImportError:
    import importlib_resources as resources


def load_rules() -> List[Dict[str, Any]]:
    """Loads anti-AI linguistic rules from package data via importlib.resources."""
    try:
        data_file = resources.files("careerforge.data").joinpath("anti_ai_rules.yaml")
        with data_file.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content.get("rules", [])
    except Exception:
        # Fallback for direct local path if package is not yet installed
        import os
        local_path = os.path.join(os.path.dirname(__file__), "..", "data", "anti_ai_rules.yaml")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content.get("rules", [])
        return []


def audit_text(text: str, rules: Optional[List[Dict[str, Any]]] = None) -> dict:
    """
    Audits an input text against peer-reviewed Anti-AI linguistic standards.
    Returns a dictionary of violations, sentence statistics, and overall score.
    """
    if rules is None:
        rules = load_rules()

    findings = []
    text_lower = text.lower()

    for rule in rules:
        rule_id = rule.get("id", "UNKNOWN")
        category = rule.get("category", "general")
        severity = rule.get("severity", "warn").upper()
        source = rule.get("source", "")
        suggestions = rule.get("suggest", {})
        patterns = rule.get("patterns", [])

        for pat in patterns:
            try:
                matches = list(re.finditer(pat, text_lower, re.IGNORECASE))
                if matches:
                    matched_texts = list({m.group(0) for m in matches})
                    for m_text in matched_texts:
                        # Find closest suggestion if available
                        sugg = suggestions.get(m_text.strip())
                        if not sugg:
                            # partial match lookup
                            for k, v in suggestions.items():
                                if k in m_text:
                                    sugg = v
                                    break
                        findings.append({
                            "rule_id": rule_id,
                            "type": category,
                            "term": m_text.strip(),
                            "count": len([m for m in matches if m.group(0) == m_text]),
                            "severity": severity,
                            "source": source,
                            "suggestion": sugg or "Use plain, active human verbs.",
                        })
            except re.error:
                continue

    # Sentence Cadence (Burstiness) Check
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences]

    avg_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    short_sentences = sum(1 for slen in sentence_lengths if slen <= 6)

    burstiness_rating = "HEALTHY"
    if sentence_lengths and short_sentences == 0 and len(sentences) > 4:
        burstiness_rating = "LOW_VARIANCE (Uniform AI cadence detected)"
        findings.append({
            "rule_id": "CADENCE-001",
            "type": "low_burstiness",
            "term": "Metronomic sentence length",
            "count": 1,
            "severity": "LOW",
            "source": "Sam Kriss (NYT 2025)",
            "suggestion": "Sentences are uniformly medium-length. Add short, punchy 3-6 word statements."
        })

    critical_count = len([f for f in findings if f["severity"] in ("CRITICAL", "ERROR")])
    is_compliant = (critical_count == 0 and len(findings) <= 2)

    return {
        "compliant": is_compliant,
        "total_issues": len(findings),
        "sentence_count": len(sentences),
        "average_sentence_words": round(avg_length, 1),
        "burstiness_status": burstiness_rating,
        "findings": findings
    }
