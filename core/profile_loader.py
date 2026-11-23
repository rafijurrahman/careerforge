"""
Candidate Profile Loader & Validator.
Reads profile.yaml or environment configurations safely.
"""

import os
import yaml

DEFAULT_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profile.yaml")
TEMPLATE_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "profile.template.yaml")

def load_profile(path: str = None) -> dict:
    """
    Loads candidate profile from specified path or default profile.yaml.
    Falls back to template if user profile does not yet exist.
    """
    target_path = path or DEFAULT_PROFILE_PATH

    if not os.path.exists(target_path):
        if os.path.exists(TEMPLATE_PROFILE_PATH):
            print(f"[Notice] '{target_path}' not found. Loading sample template from '{TEMPLATE_PROFILE_PATH}'.")
            target_path = TEMPLATE_PROFILE_PATH
        else:
            raise FileNotFoundError(f"Neither '{target_path}' nor template profile exists.")

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Basic schema validations
    required_sections = ["personal", "work_experience", "academic_background"]
    for sec in required_sections:
        if sec not in data:
            raise ValueError(f"Invalid profile schema: missing section '{sec}'.")

    return data
