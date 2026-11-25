"""
Interactive Setup Wizard for CareerForge.
Guides the user through creating their personal profile.yaml file.
"""

import os

import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(ROOT_DIR, "profile.yaml")
TEMPLATE_PATH = os.path.join(ROOT_DIR, "data", "profile.template.yaml")

def run_wizard():
    print("=" * 65)
    print("  🚀 Welcome to CareerForge: Universal Job Search & CV Engine")
    print("=" * 65)
    print("\nThis wizard will initialize your personal profile.yaml.")
    print("Your profile data remains 100% private and local on your machine.\n")

    if os.path.exists(PROFILE_PATH):
        overwrite = input("A 'profile.yaml' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Setup cancelled. Existing profile preserved.")
            return

    # Load template as baseline
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Prompt user for basic identity
    print("-" * 50)
    print("Step 1: Personal Details")
    print("-" * 50)
    name = input("Your Full Name: ").strip()
    if name:
        data["personal"]["full_name"] = name

    title = input("Target Professional Title (e.g. Frontend Engineer, Product Manager): ").strip()
    if title:
        data["personal"]["header_title"] = title
        data["target_preferences"]["target_roles"] = [title]

    email = input("Professional Email: ").strip()
    if email:
        data["personal"]["email"] = email

    phone = input("Phone Number: ").strip()
    if phone:
        data["personal"]["phone"] = phone

    location = input("Location (e.g. Dhaka, Bangladesh | Remote): ").strip()
    if location:
        data["personal"]["location"] = location

    linkedin = input("LinkedIn Profile URL: ").strip()
    if linkedin:
        data["personal"]["linkedin"] = linkedin

    github = input("GitHub Profile URL (optional): ").strip()
    if github:
        data["personal"]["github"] = github

    portfolio = input("Portfolio Website URL (optional): ").strip()
    if portfolio:
        data["personal"]["portfolio"] = portfolio

    # Write profile.yaml
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    print("\n" + "=" * 65)
    print("✅ SUCCESS: 'profile.yaml' created successfully!")
    print(f"File location: {PROFILE_PATH}")
    print("You can now open 'profile.yaml' in your editor to add your full")
    print("work experience, achievements, and technical skills.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_wizard()
