"""
CareerForge Command Line Interface (CLI).
The main entry point for setup, scraping, CV generation, and anti-AI audits.
"""

import os
import sys
import argparse
import json

from core.profile_loader import load_profile
from core.page_optimizer import optimize_to_single_page
from core.anti_ai_engine import audit_text
from scrapers.greenhouse_scanner import scan_all_greenhouse
from scrapers.ashby_scanner import scan_all_ashby
from scrapers.remotive_scanner import scan_remotive
from scrapers.work_mode_config import get_work_modes, filter_jobs_by_mode, describe_modes

def cmd_doctor(args):
    """Diagnoses system dependencies, Office/Word COM availability, and config health."""
    import platform
    import shutil

    print("\n" + "=" * 60)
    print("🩺 CareerForge Doctor — System Diagnostics")
    print("=" * 60)

    # 1. Python Check
    py_ver = sys.version.split()[0]
    py_ok = sys.version_info >= (3, 9)
    print(f"[{'PASS ✅' if py_ok else 'FAIL ❌'}] Python Version: {py_ver} (Requires 3.9+)")

    # 2. Profile Check
    profile_path = os.path.join(os.getcwd(), "profile.yaml")
    if os.path.exists(profile_path):
        try:
            prof = load_profile(profile_path)
            name = prof.get("personal", {}).get("full_name", "Unknown")
            print(f"[PASS ✅] Profile: Found 'profile.yaml' (Candidate: {name})")
        except Exception as e:
            print(f"[WARN ⚠️] Profile: 'profile.yaml' exists but failed to parse: {e}")
    else:
        print(f"[INFO ℹ️] Profile: 'profile.yaml' not found. Run 'forge init' or 'forge setup'.")

    # 3. Word COM / PDF Engine Check
    is_win = platform.system() == "Windows"
    com_ok = False
    if is_win:
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Quit()
            com_ok = True
            print("[PASS ✅] Document Engine: Microsoft Word COM is operational (Exact 1-page verification enabled)")
        except Exception:
            print("[WARN ⚠️] Document Engine: pywin32 installed but Word COM dispatch failed.")
    
    # 4. LibreOffice Fallback Check
    libre_bin = shutil.which("soffice") or shutil.which("libreoffice")
    if libre_bin:
        print(f"[PASS ✅] Fallback Engine: Headless LibreOffice found at '{libre_bin}'")
    elif not com_ok:
        print("[FAIL ❌] Fallback Engine: LibreOffice not found in PATH. Install for PDF export on Mac/Linux.")

    # 5. Core Rules & Skills Datasets
    rules_path = os.path.join(os.getcwd(), "rules", "anti_ai_rules.yaml")
    skills_path = os.path.join(os.getcwd(), "skills.yaml")
    
    print(f"[{'PASS ✅' if os.path.exists(rules_path) else 'WARN ⚠️'}] Anti-AI Rules: {'rules/anti_ai_rules.yaml loaded' if os.path.exists(rules_path) else 'Missing'}")
    print(f"[{'PASS ✅' if os.path.exists(skills_path) else 'WARN ⚠️'}] Skills Ontology: {'skills.yaml loaded' if os.path.exists(skills_path) else 'Missing'}")

    print("=" * 60 + "\n")

def cmd_setup(args):
    """Launches the interactive setup wizard."""
    from setup_wizard import run_wizard
    run_wizard()

def cmd_scrape(args):
    """Scrapes job boards for roles matching user profile or specified keywords."""
    profile = load_profile(args.profile)
    keywords = args.roles or profile.get("target_preferences", {}).get("target_roles", ["Software Engineer"])
    work_modes = get_work_modes(profile)

    print(f"\n🔍 Searching for: {', '.join(keywords)}")
    print(f"   Work mode filter: {describe_modes(work_modes)}")
    print(f"   Sources: Greenhouse | Ashby | Remotive\n")

    gh_matches    = scan_all_greenhouse(keywords=keywords, exclude_senior=not args.include_senior)
    ashby_matches = scan_all_ashby(keywords=keywords, exclude_senior=not args.include_senior)
    rem_matches   = scan_remotive(target_roles=keywords, limit=args.limit)

    all_matches = gh_matches + ashby_matches + rem_matches

    # Apply work mode filter
    if work_modes and work_modes != ["Remote"]:
        all_matches = filter_jobs_by_mode(all_matches, work_modes)

    print(f"✨ Found {len(all_matches)} matching opportunities:\n")

    for idx, j in enumerate(all_matches[: args.limit], 1):
        source = j.get("platform") or j.get("source", "Board")
        print(f"{idx}. [{source}] {j['title']} @ {j['company']}")
        print(f"   Location: {j.get('location', 'Remote')}")
        print(f"   Apply: {j['url']}\n")

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(all_matches, f, indent=2)
        print(f"💾 Results saved to '{args.save}'.")

def cmd_apply(args):
    """Generates and optimizes a 1-page ATS CV from the candidate profile."""
    profile = load_profile(args.profile)
    out_dir = args.out or os.path.join(os.getcwd(), "output")
    os.makedirs(out_dir, exist_ok=True)

    name_slug = profile.get("personal", {}).get("full_name", "Candidate").replace(" ", "_")
    role_slug = args.role_tag or "Universal"
    
    docx_file = os.path.join(out_dir, f"{name_slug}_{role_slug}_CV.docx")
    pdf_file = os.path.join(out_dir, f"{name_slug}_{role_slug}_CV.pdf")

    print(f"\n📄 Building ATS-optimized CV for {profile.get('personal', {}).get('full_name')}...")
    config = optimize_to_single_page(profile, docx_file, pdf_file, target_pages=args.pages)

    print("\n" + "=" * 60)
    print("✅ SUCCESS: 1-Page ATS CV generated and verified!")
    print(f"   DOCX: {docx_file}")
    print(f"   PDF:  {pdf_file}")
    print(f"   Pages: {config.get('pages', 1)} | Font Scale: {config.get('font_scale')}")
    print("=" * 60 + "\n")

def cmd_audit(args):
    """Runs a linguistic Anti-AI audit on the provided text file."""
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.")
        return

    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    res = audit_text(content)
    print("\n" + "=" * 60)
    print("🛡️ Anti-AI Linguistic Audit Report")
    print("=" * 60)
    print(f"Compliant:            {'YES ✅' if res['compliant'] else 'NO ⚠️'}")
    print(f"Total Issues:         {res['total_issues']}")
    print(f"Average Sentence:     {res['average_sentence_words']} words")
    print(f"Burstiness Cadence:   {res['burstiness_status']}")
    
    if res['findings']:
        print("\nFindings:")
        for idx, item in enumerate(res['findings'], 1):
            term = item.get('term') or item.get('message')
            print(f"  {idx}. [{item['severity']}] {item['type'].upper()}: '{term}'")
    else:
        print("\n🎉 Zero AI buzzwords detected. Clean human-voice phrasing!")
    print("=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(
        prog="careerforge",
        description="CareerForge: Universal, Role-Agnostic Job Application & CV Optimization Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Run system diagnostics for Word COM, LibreOffice, and profile")
    p_doc.set_defaults(func=cmd_doctor)

    # init / setup
    p_init = subparsers.add_parser("init", help="Initialize your candidate profile (alias for setup)")
    p_init.set_defaults(func=cmd_setup)

    p_setup = subparsers.add_parser("setup", help="Initialize your candidate profile")
    p_setup.set_defaults(func=cmd_setup)

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Search top remote and tech job boards")
    p_scrape.add_argument("--profile", type=str, default=None, help="Path to profile.yaml")
    p_scrape.add_argument("--roles", nargs="+", default=None, help="Specific role keywords to search")
    p_scrape.add_argument("--include-senior", action="store_true", help="Include senior/lead/director roles")
    p_scrape.add_argument("--limit", type=int, default=15, help="Number of jobs to display")
    p_scrape.add_argument("--save", type=str, default=None, help="Save results to JSON file")
    p_scrape.set_defaults(func=cmd_scrape)

    # apply
    p_apply = subparsers.add_parser("apply", help="Build and verify a 1-page ATS CV")
    p_apply.add_argument("--profile", type=str, default=None, help="Path to profile.yaml")
    p_apply.add_argument("--out", type=str, default=None, help="Output directory")
    p_apply.add_argument("--role-tag", type=str, default="Tailored", help="Role tag for file naming")
    p_apply.add_argument("--pages", type=int, default=1, help="Target page count (default: 1)")
    p_apply.set_defaults(func=cmd_apply)

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit a text file against Anti-AI standards")
    p_audit.add_argument("--file", type=str, required=True, help="Path to text or markdown file")
    p_audit.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)

if __name__ == "__main__":
    main()
