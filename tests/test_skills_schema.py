"""
Validates skills ontology schema and ensures no duplicate aliases exist across canonical skills.
"""

from importlib import resources

import pytest
import yaml


def test_skills_schema_and_alias_uniqueness():
    ref = resources.files("careerforge.data").joinpath("skills.yaml")
    assert ref.is_file(), "skills.yaml must be bundled in package data"

    with ref.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict)
    alias_to_canonical = {}

    for category_name, skills_dict in data.items():
        assert isinstance(skills_dict, dict), f"Category '{category_name}' must be a mapping of skill entries"
        for skill_key, skill_info in skills_dict.items():
            assert "canonical" in skill_info, f"Skill '{skill_key}' missing 'canonical'"
            assert "aliases" in skill_info, f"Skill '{skill_key}' missing 'aliases'"
            assert isinstance(skill_info["aliases"], list), f"Skill '{skill_key}' aliases must be a list"

            canonical = skill_info["canonical"]
            # Self alias check
            for alias in skill_info["aliases"]:
                alias_lower = alias.strip().lower()
                if alias_lower in alias_to_canonical:
                    existing_canonical = alias_to_canonical[alias_lower]
                    if existing_canonical != canonical:
                        pytest.fail(
                            f"Duplicate alias '{alias_lower}' found for both "
                            f"'{existing_canonical}' and '{canonical}'"
                        )
                alias_to_canonical[alias_lower] = canonical
