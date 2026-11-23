"""
Positive and negative test cases for each anti-AI rule.
"""

import pytest

from careerforge.core.anti_ai_engine import audit_text, load_rules


@pytest.fixture(scope="module")
def all_rules():
    return load_rules()


def test_audit_positive_and_negative_for_all_rules(all_rules):
    # Rule AI-001 (Puffery): positive case contains 'delve', negative uses 'explore'
    res_pos_001 = audit_text("We delve into complex architectures.")
    assert any(f["rule_id"] == "AI-001" for f in res_pos_001["findings"])
    res_neg_001 = audit_text("I explored the codebase and fixed the memory leak.")
    assert not any(f["rule_id"] == "AI-001" for f in res_neg_001["findings"])

    # Rule AI-002 (Copula avoidance): positive contains 'serves as a', negative uses 'is'
    res_pos_002 = audit_text("Ubuntu serves as the default deployment image.")
    assert any(f["rule_id"] == "AI-002" for f in res_pos_002["findings"])
    res_neg_002 = audit_text("Ubuntu is the default deployment image.")
    assert not any(f["rule_id"] == "AI-002" for f in res_neg_002["findings"])

    # Rule AI-003 (Robotic transitions): positive contains 'Furthermore,', negative uses 'Also,'
    res_pos_003 = audit_text("Furthermore, the database latency dropped significantly.")
    assert any(f["rule_id"] == "AI-003" for f in res_pos_003["findings"])
    res_neg_003 = audit_text("The database latency also dropped significantly.")
    assert not any(f["rule_id"] == "AI-003" for f in res_neg_003["findings"])

    # Rule AI-004 (Participial suffix): positive contains ', ensuring', negative uses separate sentence
    res_pos_004 = audit_text("I refactored the auth pipeline, ensuring 99.9% uptime.")
    assert any(f["rule_id"] == "AI-004" for f in res_pos_004["findings"])
    res_neg_004 = audit_text("I refactored the auth pipeline. This achieved 99.9% uptime.")
    assert not any(f["rule_id"] == "AI-004" for f in res_neg_004["findings"])

    # Rule AI-005 (Negative parallelism): positive contains 'not only ... but also'
    res_pos_005 = audit_text("He not only wrote the API but also managed deployments.")
    assert any(f["rule_id"] == "AI-005" for f in res_pos_005["findings"])
    res_neg_005 = audit_text("He wrote the API and managed deployments.")
    assert not any(f["rule_id"] == "AI-005" for f in res_neg_005["findings"])


def test_clean_human_voice_text_passes_audit():
    clean_text = """
    I built the patient intake system with SQL and Power BI. It handled 10,000 records.
    The daily report took 30 minutes instead of two hours.
    I audited weekly logs to prevent billing mismatches.
    """
    res = audit_text(clean_text)
    assert res["compliant"] is True
    assert res["total_issues"] == 0
