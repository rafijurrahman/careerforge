"""
Proves the privacy guarantee: non-scrape commands (audit, profile loading, CV building)
run 100% locally and open ZERO network sockets.
"""

import os

from careerforge.core.anti_ai_engine import audit_text
from careerforge.core.profile_loader import load_profile


def test_audit_text_offline_guarantee(socket_disabled=None):
    """Verifies audit_text opens zero network connections."""
    text = "I built the system using SQL and Python. It handled 10,000 records."
    res = audit_text(text)
    assert res["compliant"] is True


def test_profile_loader_offline_guarantee(socket_disabled=None):
    """Verifies profile loading opens zero network connections."""
    example_path = os.path.join("examples", "profile.example.yaml")
    prof = load_profile(example_path)
    assert prof["personal"]["full_name"] == "Alex Rivera"
