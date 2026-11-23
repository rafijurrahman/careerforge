"""
CareerForge Command Line Interface (CLI).
The main entry point for setup, diagnostics, scraping, CV generation, and anti-AI audits.
"""

import argparse
import json
import os
import platform
import shutil
import sys
from importlib import resources

try:
    from careerforge.core.anti_ai_engine import audit_text
    from careerforge.core.dorks import generate_ats_dorks
    from careerforge.core.matcher import compute_ats_match
    from careerforge.core.page_optimizer import optimize_to_single_page
    from careerforge.core.profile_loader import load_profile
    from careerforge.core.tailor_engine import tailor_profile
    from careerforge.scrapers.ashby_scanner import scan_all_ashby
    from careerforge.scrapers.greenhouse_scanner import scan_all_greenhouse
    from careerforge.scrapers.remotive_scanner import scan_remotive
    from careerforge.scrapers.work_mode_config import (
        describe_modes,
        filter_jobs_by_mode,
        get_work_modes,
    )
except ImportError:
    from core.anti_ai_engine import audit_text
    from core.dorks import generate_ats_dorks
    from core.matcher import compute_ats_match
    from core.page_optimizer import optimize_to_single_page
    from core.profile_loader import load_profile
    from core.tailor_engine import tailor_profile
    from scrapers.ashby_scanner import scan_all_ashby
    from scrapers.greenhouse_scanner import scan_all_greenhouse
    from scrapers.remotive_scanner import scan_remotive
    from scrapers.work_mode_config import describe_modes, filter_jobs_by_mode, get_work_modes


def cmd_doctor(args):
    """Diagnoses system dependencies, Office/Word COM availability, and config health."""
    results = {
        "python": {"version": sys.version.split()[0], "ok": sys.version_info >= (3, 10)},
        "profile": {"found": False, "valid": False, "candidate": None, "hint": None},
        "pdf_engine": {"word_com": False, "libreoffice": False, "active_backend": None, "hints": []},
        "package_data": {"rules": False, "skills": False},
        "overall_ok": True,
    }

    # 1. Python check
    if not results["python"]["ok"]:
        results["overall_ok"] = False

    # 2. Profile check
    profile_path = os.path.join(os.getcwd(), "profile.yaml")
    if os.path.exists(profile_path):
        results["profile"]["found"] = True
        try:
            prof = load_profile(profile_path)
            results["profile"]["valid"] = True
            results["profile"]["candidate"] = prof.get("personal", {}).get("full_name", "Unknown")
        except Exception as e:
            results["profile"]["hint"] = f"Failed to parse profile.yaml: {e}"
            results["overall_ok"] = False
    else:
        results["profile"]["hint"] = "Run 'forge init' or 'forge setup' to create your profile.yaml"

    # 3. Document / PDF Engine Check
    is_win = sys.platform == "win32"
    is_linux = sys.platform.startswith("linux")

    if is_linux:
        results["platform_notice"] = "Linux is community-supported; unit tests pass, page-fit is not officially tested."

    if is_win:
        try:
            import win32com.client
            word = win32com.client.DispatchEx("Word.Application")
            word.Quit()
            results["pdf_engine"]["word_com"] = True
            results["pdf_engine"]["active_backend"] = "Microsoft Word COM (Fast-path)"
        except Exception:
            results["pdf_engine"]["hints"].append(
                "Windows Word COM unavailable. For optional fast-path, ensure Microsoft Word is installed and run: pip install pywin32"
            )

    try:
        from careerforge.core.page_optimizer import find_libreoffice_bin
        libre_bin = find_libreoffice_bin()
    except Exception:
        libre_bin = shutil.which("soffice") or shutil.which("libreoffice")

    if libre_bin:
        results["pdf_engine"]["libreoffice"] = True
        if not results["pdf_engine"]["active_backend"]:
            results["pdf_engine"]["active_backend"] = f"LibreOffice Headless ({libre_bin})"

    if not results["pdf_engine"]["word_com"] and not results["pdf_engine"]["libreoffice"]:
        results["overall_ok"] = False
        os_name = platform.system()
        if os_name == "Windows":
            hint = "Install LibreOffice: winget install TheDocumentFoundation.LibreOffice"
        elif os_name == "Darwin":
            hint = "Install LibreOffice: brew install --cask libreoffice"
        else:
            hint = "Install LibreOffice: sudo apt-get install -y libreoffice-writer"
        results["pdf_engine"]["hints"].append(hint)

    # 4. Package Data Check
    try:
        rules_ref = resources.files("careerforge.data").joinpath("anti_ai_rules.yaml")
        results["package_data"]["rules"] = rules_ref.is_file()
    except Exception:
        results["package_data"]["rules"] = os.path.exists(os.path.join("careerforge", "data", "anti_ai_rules.yaml"))

    try:
        skills_ref = resources.files("careerforge.data").joinpath("skills.yaml")
        results["package_data"]["skills"] = skills_ref.is_file()
    except Exception:
        results["package_data"]["skills"] = os.path.exists(os.path.join("careerforge", "data", "skills.yaml"))

    if not results["package_data"]["rules"] or not results["package_data"]["skills"]:
        results["overall_ok"] = False

    # Output formatting
    if getattr(args, "json", False):
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["overall_ok"] else 1)

    print("\n" + "=" * 60)
    print("🩺 CareerForge Doctor — System Diagnostics")
    print("=" * 60)

    py_status = "PASS ✅" if results["python"]["ok"] else "FAIL ❌"
    print(f"[{py_status}] Python Version: {results['python']['version']} (Requires >= 3.10)")

    if is_linux:
        print("[INFO ℹ️] Platform: Linux (Community-supported; page-fit is best-effort)")

    if results["profile"]["found"] and results["profile"]["valid"]:
        print(f"[PASS ✅] Profile: Found 'profile.yaml' (Candidate: {results['profile']['candidate']})")
    elif results["profile"]["found"]:
        print("[WARN ⚠️] Profile: 'profile.yaml' exists but has syntax issues.")
        print(f"         → {results['profile']['hint']}")
    else:
        print("[INFO ℹ️] Profile: 'profile.yaml' not found.")
        print(f"         → {results['profile']['hint']}")

    if results["pdf_engine"]["active_backend"]:
        print(f"[PASS ✅] Document Engine: {results['pdf_engine']['active_backend']}")
    else:
        print("[WARN ⚠️] Document Engine: No PDF engine detected (Word COM or LibreOffice).")
        for hint in results["pdf_engine"]["hints"]:
            print(f"         → {hint}")

    rules_st = "PASS ✅" if results["package_data"]["rules"] else "FAIL ❌"
    skills_st = "PASS ✅" if results["package_data"]["skills"] else "FAIL ❌"
    print(f"[{rules_st}] Anti-AI Rules: {'Bundled in package' if results['package_data']['rules'] else 'Missing'}")
    print(f"[{skills_st}] Skills Ontology: {'Bundled in package' if results['package_data']['skills'] else 'Missing'}")
    print("=" * 60 + "\n")

    sys.exit(0 if results["overall_ok"] else 1)


def cmd_setup(args):
    """Launches the interactive setup wizard."""
    try:
        from careerforge.setup_wizard import run_wizard
    except ImportError:
        from setup_wizard import run_wizard
    run_wizard()


def cmd_scrape(args):
    """Scrapes job boards for roles matching user profile or specified keywords."""
    profile = load_profile(args.profile)
    keywords = args.roles or profile.get("target_preferences", {}).get("target_roles", ["Software Engineer"])
    work_modes = get_work_modes(profile)

    print(f"\n🔍 Searching for: {', '.join(keywords)}")
    print(f"   Work mode filter: {describe_modes(work_modes)}")
    print("   Sources: Greenhouse | Ashby | Remotive\n")

    gh_matches = scan_all_greenhouse(keywords=keywords, exclude_senior=not args.include_senior)
    ashby_matches = scan_all_ashby(keywords=keywords, exclude_senior=not args.include_senior)
    rem_matches = scan_remotive(target_roles=keywords, limit=args.limit)

    all_matches = gh_matches + ashby_matches + rem_matches

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


def cmd_match(args):
    """Computes keyword match and ATS skill gap against a job description."""
    profile = load_profile(args.profile)
    jd_content = ""
    if os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()
    else:
        jd_content = args.jd

    res = compute_ats_match(jd_content, profile)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        sys.exit(0)

    print("\n" + "=" * 60)
    print("🎯 ATS Keyword Match & Gap Analysis")
    print("=" * 60)
    print(f"Overall Match Score:  {res['match_percentage']}%")
    print(f"Matched Skills ({res['matched_count']}):   {', '.join(res['matched_skills']) if res['matched_skills'] else 'None'}")
    print(f"Missing Skills ({res['missing_count']}):   {', '.join(res['missing_skills']) if res['missing_skills'] else 'None'}")
    if res["additional_skills"]:
        print(f"Additional Skills ({len(res['additional_skills'])}): {', '.join(res['additional_skills'][:10])}")
    print("=" * 60 + "\n")


def cmd_tailor(args):
    """Tailors master profile bullets to match a job description and generates a 1-page CV."""
    profile = load_profile(args.profile)
    jd_content = ""
    if os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()
    else:
        jd_content = args.jd

    print("\n🎯 Analyzing job requirements & tailoring profile bullets...")
    tailored_prof, report = tailor_profile(
        profile,
        jd_content,
        max_bullets_per_role=args.max_bullets or 4,
    )

    out_dir = args.out or os.path.join(os.getcwd(), "output", "tailored")
    os.makedirs(out_dir, exist_ok=True)

    name_slug = profile.get("personal", {}).get("full_name", "Candidate").replace(" ", "_")
    role_slug = args.role_tag or "Tailored"

    docx_file = os.path.join(out_dir, f"{name_slug}_{role_slug}_CV.docx")
    pdf_file = os.path.join(out_dir, f"{name_slug}_{role_slug}_CV.pdf")

    config = optimize_to_single_page(
        tailored_prof,
        docx_file,
        pdf_file,
        target_pages=args.pages,
        engine=args.engine,
    )

    report["output_docx"] = docx_file
    report["output_pdf"] = pdf_file
    report["page_fit"] = config

    if getattr(args, "json", False):
        print(json.dumps(report, indent=2))
        sys.exit(0)

    print("\n" + "=" * 60)
    print("✨ Tailored 1-Page ATS CV Successfully Generated!")
    print("=" * 60)
    print(f"Candidate:            {profile.get('personal', {}).get('full_name')}")
    print(f"Initial Match:        {report['initial_match_percentage']}%")
    print(f"Tailored Match:       {report['tailored_match_percentage']}%")
    print(f"Matched Skills:       {', '.join(report['matched_skills'][:8])}")
    if report["missing_skills"]:
        print(f"Missing Skills:       {', '.join(report['missing_skills'][:6])}")
    print("-" * 60)
    print(f"DOCX:                 {docx_file}")
    print(f"PDF:                  {pdf_file}")
    print(f"Pages:                {config.get('pages', 1)} | Font Scale: {config.get('font_scale')}")
    print(f"Backend Engine:       {config.get('backend', 'Default')}")
    print("=" * 60 + "\n")


def cmd_dorks(args):
    """Generates direct-to-employer Google ATS search queries."""
    dorks = generate_ats_dorks(args.role, location=args.location or "remote", extra_keywords=args.skills or "")

    if getattr(args, "json", False):
        print(json.dumps(dorks, indent=2))
        sys.exit(0)

    print("\n" + "=" * 60)
    print(f"🔎 Direct Employer ATS Search Dorks for '{args.role}' ({args.location or 'remote'})")
    print("=" * 60)
    for idx, d in enumerate(dorks, 1):
        print(f"\n{idx}. [{d['platform']}] {d['description']}")
        print(f"   Query: {d['dork']}")
        print(f"   URL:   {d['url']}")
    print("\n" + "=" * 60 + "\n")


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
    config = optimize_to_single_page(profile, docx_file, pdf_file, target_pages=args.pages, engine=args.engine)

    print("\n" + "=" * 60)
    print("✅ SUCCESS: 1-Page ATS CV generated!")
    print(f"   DOCX: {docx_file}")
    print(f"   PDF:  {pdf_file}")
    print(f"   Pages: {config.get('pages', 1)} | Font Scale: {config.get('font_scale')}")
    print(f"   Engine: {config.get('backend', 'Default')}")
    print("=" * 60 + "\n")


def cmd_audit(args):
    """Runs a linguistic Anti-AI audit on the provided text file."""
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading '{args.file}': {e}", file=sys.stderr)
        sys.exit(2)

    res = audit_text(content)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["compliant"] else 1)

    print("\n" + "=" * 60)
    print("🛡️ Anti-AI Linguistic Audit Report")
    print("=" * 60)
    print(f"Compliant:            {'YES ✅' if res['compliant'] else 'NO ⚠️'}")
    print(f"Total Issues:         {res['total_issues']}")
    print(f"Sentence Count:       {res['sentence_count']}")
    print(f"Average Sentence:     {res['average_sentence_words']} words")
    print(f"Burstiness Cadence:   {res['burstiness_status']}")

    if res["findings"]:
        print("\nFindings:")
        for idx, item in enumerate(res["findings"], 1):
            term = item.get("term")
            rule_id = item.get("rule_id", "AI-RULE")
            sugg = item.get("suggestion", "")
            print(f"  {idx}. [{item['severity']}] {rule_id}: '{term}'")
            if sugg:
                print(f"     → Suggestion: {sugg}")
    else:
        print("\n🎉 Zero AI puffery detected. Clean human-voice phrasing!")
    print("=" * 60 + "\n")

    sys.exit(0 if res["compliant"] else 1)


def main():
    parser = argparse.ArgumentParser(
        prog="careerforge",
        description="CareerForge: Universal, Role-Agnostic Job Application & CV Optimization Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # doctor
    p_doc = subparsers.add_parser("doctor", help="Run system diagnostics for Word COM, LibreOffice, and config")
    p_doc.add_argument("--json", action="store_true", help="Output diagnostic report as JSON")
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
    p_apply.add_argument(
        "--engine",
        choices=["auto", "word", "libreoffice"],
        default="auto",
        help="PDF conversion & page-fit engine: auto (Word COM on Windows, LibreOffice on macOS), word, or libreoffice",
    )
    p_apply.set_defaults(func=cmd_apply)

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit a text file against Anti-AI standards")
    p_audit.add_argument("--file", type=str, required=True, help="Path to text or markdown file")
    p_audit.add_argument("--json", action="store_true", help="Output audit report as JSON")
    p_audit.set_defaults(func=cmd_audit)

    # match
    p_match = subparsers.add_parser("match", help="Analyze ATS keyword gap against a job description")
    p_match.add_argument("--jd", type=str, required=True, help="Path to job description file or raw text string")
    p_match.add_argument("--profile", type=str, default=None, help="Path to profile.yaml")
    p_match.add_argument("--json", action="store_true", help="Output match report as JSON")
    p_match.set_defaults(func=cmd_match)

    # tailor
    p_tailor = subparsers.add_parser("tailor", help="Auto-tailor master profile bullets to match a job description")
    p_tailor.add_argument("--jd", type=str, required=True, help="Path to job description file or raw text string")
    p_tailor.add_argument("--profile", type=str, default=None, help="Path to profile.yaml")
    p_tailor.add_argument("--out", type=str, default=None, help="Output directory")
    p_tailor.add_argument("--role-tag", type=str, default="Tailored", help="Role tag for file naming")
    p_tailor.add_argument("--max-bullets", type=int, default=4, help="Max bullets per role (default: 4)")
    p_tailor.add_argument("--pages", type=int, default=1, help="Target page count (default: 1)")
    p_tailor.add_argument(
        "--engine",
        choices=["auto", "word", "libreoffice"],
        default="auto",
        help="PDF conversion & page-fit engine: auto, word, or libreoffice",
    )
    p_tailor.add_argument("--json", action="store_true", help="Output tailoring report as JSON")
    p_tailor.set_defaults(func=cmd_tailor)

    # dorks
    p_dorks = subparsers.add_parser("dorks", help="Generate high-precision Google search queries for ATS boards")
    p_dorks.add_argument("role", type=str, help="Target role title (e.g. 'Data Analyst', 'Backend Engineer')")
    p_dorks.add_argument("--location", type=str, default="remote", help="Location or work mode filter (default: 'remote')")
    p_dorks.add_argument("--skills", type=str, default="", help="Additional comma-separated skills to include")
    p_dorks.add_argument("--json", action="store_true", help="Output dorks as JSON")
    p_dorks.set_defaults(func=cmd_dorks)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
