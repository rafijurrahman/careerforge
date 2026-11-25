"""
Candidate Profile Loader & Validator.
Reads profile.yaml or environment configurations safely.
"""

import os

import yaml

DEFAULT_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profile.yaml")
TEMPLATE_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "profile.template.yaml")

def load_profile(path: str = None) -> dict:
    """
    Loads candidate profile from specified path or profile.yaml in the current directory.
    Raises FileNotFoundError with a 'forge init' hint if missing.
    """
    if path:
        target_path = path
        if not os.path.exists(target_path):
            raise FileNotFoundError(
                f"Profile file '{target_path}' not found. Run 'forge init' to create profile.yaml or pass --profile <path>."
            )
    else:
        cwd_profile = os.path.join(os.getcwd(), "profile.yaml")
        if os.path.exists(cwd_profile):
            target_path = cwd_profile
        elif os.path.exists(DEFAULT_PROFILE_PATH):
            target_path = DEFAULT_PROFILE_PATH
        else:
            raise FileNotFoundError(
                "Profile 'profile.yaml' not found in current directory. Run 'forge init' to create your profile, or pass --profile <path>."
            )

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
