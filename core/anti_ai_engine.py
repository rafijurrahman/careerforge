"""
Anti-AI Linguistic Audit & Sanitization Engine.
Implements rules derived from computational linguistics research (PNAS, Science Advances, ACL).
"""

import re

BANNED_WORDS = [
    "delve", "delves", "delving", "underscore", "underscores", "underscoring",
    "intricate", "meticulously", "pivotal", "bolster", "bolstered", "tapestry",
    "landscape", "realm", "beacon", "foster", "fostering", "cultivate",
    "unrivaled", "groundbreaking", "paramount", "resonate", "resonates",
    "seamless", "seamlessly", "showcase", "showcasing", "transformative",
    "indelible mark", "deeply rooted", "cornerstone", "multifaceted", "dynamic",
    "evolving", "leverage", "complexities", "interplay", "burgeoning"
]

BANNED_TRANSITIONS = [
    "furthermore", "moreover", "additionally", "consequently",
    "it is worth noting that", "it is important to remember that",
    "in conclusion", "to summarize", "when it comes to"
]

COPULA_INFLATIONS = [
    "serves as a", "marks the", "stands as a", "acts as a", "functions as a"
]

def audit_text(text: str) -> dict:
    """
    Audits an input text against peer-reviewed Anti-AI linguistic standards.
    Returns a dictionary of violations and overall score.
    """
    findings = []
    text_lower = text.lower()

    # 1. Check Banned Vocabulary
    for word in BANNED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            findings.append({
                "type": "banned_vocabulary",
                "term": word,
                "count": len(matches),
                "severity": "CRITICAL"
            })

    # 2. Check Banned Transitions
    for trans in BANNED_TRANSITIONS:
        if trans in text_lower:
            findings.append({
                "type": "robotic_transition",
                "term": trans,
                "severity": "HIGH"
            })

    # 3. Check Copula Inflation
    for cop in COPULA_INFLATIONS:
        if cop in text_lower:
            findings.append({
                "type": "copula_inflation",
                "term": cop,
                "suggestion": "Replace with direct 'is' or 'are'",
                "severity": "MEDIUM"
            })

    # 4. Check Sentence Cadence (Burstiness)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_lengths = [len(s.split()) for s in sentences]
    
    avg_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
    short_sentences = sum(1 for l in sentence_lengths if l <= 6)
    
    burstiness_rating = "HEALTHY"
    if sentence_lengths and short_sentences == 0 and len(sentences) > 4:
        burstiness_rating = "LOW_VARIANCE (Uniform AI cadence detected)"
        findings.append({
            "type": "low_burstiness",
            "message": "Sentences are uniformly medium-length. Add short, punchy 3-6 word statements.",
            "severity": "LOW"
        })

    is_compliant = len([f for f in findings if f["severity"] == "CRITICAL"]) == 0

    return {
        "compliant": is_compliant,
        "total_issues": len(findings),
        "sentence_count": len(sentences),
        "average_sentence_words": round(avg_length, 1),
        "burstiness_status": burstiness_rating,
        "findings": findings
    }
