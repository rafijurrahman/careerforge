"""
Tests validation and regex sanity of anti_ai_rules.yaml.
"""

import re
from importlib import resources

import pytest
import yaml


def test_rules_file_exists_and_parses():
    ref = resources.files("careerforge.data").joinpath("anti_ai_rules.yaml")
    assert ref.is_file(), "anti_ai_rules.yaml must be bundled in package data"
    with ref.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "rules" in data
    assert len(data["rules"]) > 0


def test_rules_schema_and_unique_ids():
    ref = resources.files("careerforge.data").joinpath("anti_ai_rules.yaml")
    with ref.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    rules = data["rules"]
    seen_ids = set()

    for rule in rules:
        # 1. Required fields
        for field in ("id", "category", "severity", "source", "patterns", "suggest"):
            assert field in rule, f"Rule {rule.get('id', 'MISSING_ID')} is missing field '{field}'"

        # 2. Unique ID
        rule_id = rule["id"]
        assert rule_id not in seen_ids, f"Duplicate rule ID found: '{rule_id}'"
        seen_ids.add(rule_id)

        # 3. Severity is valid
        assert rule["severity"] in ("warn", "error", "critical"), f"Invalid severity in rule {rule_id}"

        # 4. Patterns list is non-empty and every pattern compiles
        patterns = rule["patterns"]
        assert isinstance(patterns, list) and len(patterns) > 0, f"Rule {rule_id} has empty patterns"
        for pat in patterns:
            try:
                re.compile(pat)
            except re.error as e:
                pytest.fail(f"Regex pattern '{pat}' in rule {rule_id} failed to compile: {e}")

        # 5. Suggest mapping is non-empty
        suggest = rule["suggest"]
        assert isinstance(suggest, dict) and len(suggest) > 0, f"Rule {rule_id} has empty suggest mapping"
