"""
Validates that examples/profile.example.yaml loads and conforms to profile schema.
"""

import os

from careerforge.core.profile_loader import load_profile


def test_example_profile_loads_and_validates():
    example_path = os.path.join("examples", "profile.example.yaml")
    assert os.path.exists(example_path), "examples/profile.example.yaml must exist"

    prof = load_profile(example_path)

    # 1. Personal section
    personal = prof.get("personal", {})
    assert personal.get("full_name") == "Alex Rivera"
    assert "email" in personal
    assert "location" in personal

    # 2. Target preferences
    prefs = prof.get("target_preferences", {})
    assert isinstance(prefs.get("target_roles"), list)
    assert len(prefs["target_roles"]) > 0

    # 3. Experience section
    exp = prof.get("experience", [])
    assert isinstance(exp, list) and len(exp) >= 1
    for role in exp:
        assert "title" in role
        assert "company" in role
        assert "bullets" in role
        assert len(role["bullets"]) > 0

    # 4. Education and skills
    assert len(prof.get("education", [])) >= 1
    assert "skills" in prof
