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

    # Normalize section aliases
    if "experience" in data and "work_experience" not in data:
        data["work_experience"] = data["experience"]
    if "work_experience" in data and "experience" not in data:
        data["experience"] = data["work_experience"]

    if "education" in data and "academic_background" not in data:
        data["academic_background"] = data["education"]
    if "academic_background" in data and "education" not in data:
        data["education"] = data["academic_background"]

    # Basic schema validations
    if "personal" not in data:
        raise ValueError("Invalid profile schema: missing section 'personal'.")
    if not data.get("work_experience") and not data.get("experience"):
        raise ValueError("Invalid profile schema: missing section 'work_experience' or 'experience'.")
    if not data.get("academic_background") and not data.get("education"):
        raise ValueError("Invalid profile schema: missing section 'academic_background' or 'education'.")

    return data
