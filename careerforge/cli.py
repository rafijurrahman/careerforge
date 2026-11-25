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

# Ensure UTF-8 output across all consoles and CI runners to prevent cp1252 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from careerforge.core.anti_ai_engine import audit_text
    from careerforge.core.ats_sim import AtsSimFileError, run_ats_sim
    from careerforge.core.dorks import generate_ats_dorks
    from careerforge.core.eligibility import check_eligibility
    from careerforge.core.ghost import analyze_ghost_jobs
    from careerforge.core.matcher import compute_ats_match
    from careerforge.core.page_optimizer import optimize_to_single_page
    from careerforge.core.profile_loader import load_profile
    from careerforge.core.reporter import ReportError, generate_report
    from careerforge.core.salary import SalaryError, analyze_salaries
    from careerforge.core.store import VALID_STAGES, CareerStore, StoreError
    from careerforge.core.tailor_engine import tailor_profile
    from careerforge.scrapers.ashby_scanner import AshbyScraper
    from careerforge.scrapers.greenhouse_scanner import GreenhouseScraper
    from careerforge.scrapers.lever_scanner import LeverScraper
    from careerforge.scrapers.remotive_scanner import RemotiveScraper
    from careerforge.scrapers.work_mode_config import (
        describe_modes,
        get_work_modes,
        location_matches,
    )
except ImportError:
    from core.anti_ai_engine import audit_text
    from core.ats_sim import AtsSimFileError, run_ats_sim
    from core.dorks import generate_ats_dorks
    from core.eligibility import check_eligibility
    from core.ghost import analyze_ghost_jobs
    from core.matcher import compute_ats_match
    from core.page_optimizer import optimize_to_single_page
    from core.profile_loader import load_profile
    from core.reporter import ReportError, generate_report
    from core.salary import SalaryError, analyze_salaries
    from core.store import VALID_STAGES, CareerStore, StoreError
    from core.tailor_engine import tailor_profile
    from scrapers.ashby_scanner import AshbyScraper
    from scrapers.greenhouse_scanner import GreenhouseScraper
    from scrapers.lever_scanner import LeverScraper
    from scrapers.remotive_scanner import RemotiveScraper
    from scrapers.work_mode_config import (
        describe_modes,
        get_work_modes,
        location_matches,
    )


def _load_profile_or_exit(path: str = None) -> dict:
    """Loads profile.yaml or exits cleanly with status code 2 and a forge init hint."""
    try:
        return load_profile(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


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
    if args.roles and not args.profile:
        try:
            profile = load_profile(None)
            work_modes = get_work_modes(profile)
        except FileNotFoundError:
            profile = {}
            work_modes = ["Remote"]
        keywords = args.roles
    else:
        profile = _load_profile_or_exit(args.profile)
        keywords = args.roles or profile.get("target_preferences", {}).get("target_roles", ["Software Engineer"])
        work_modes = get_work_modes(profile)

    print(f"\n🔍 Searching for: {', '.join(keywords)}")
    print(f"   Work mode filter: {describe_modes(work_modes)}")
    print("   Sources: Greenhouse | Ashby | Lever | Remotive\n")

    gh_scraper = GreenhouseScraper()
    ashby_scraper = AshbyScraper()
    lever_scraper = LeverScraper()
    rem_scraper = RemotiveScraper()

    gh_postings, gh_ok, _ = gh_scraper.fetch_with_status({"keywords": keywords, "exclude_senior": not args.include_senior})
    ashby_postings, ashby_ok, _ = ashby_scraper.fetch_with_status({"keywords": keywords, "exclude_senior": not args.include_senior})
    lever_postings, lever_ok, _ = lever_scraper.fetch_with_status({"keywords": keywords, "exclude_senior": not args.include_senior})
    rem_postings = list(rem_scraper.fetch({"target_roles": keywords, "limit": args.limit}))

    all_postings = gh_postings + ashby_postings + lever_postings + rem_postings
    if work_modes and work_modes != ["Remote"]:
        all_postings = [p for p in all_postings if location_matches(p.location, work_modes)]

    my_country = getattr(args, "my_country", None)
    stats = None
    store = None
    if args.save:
        succeeded_boards = {}
        succeeded_boards.update(gh_ok)
        succeeded_boards.update(ashby_ok)
        succeeded_boards.update(lever_ok)
        store = CareerStore()
        stats = store.upsert_scraped_jobs(all_postings, succeeded_boards=succeeded_boards)

    all_matches = []
    for p in all_postings:
        elig = check_eligibility(f"{p.location} {p.description or ''}", my_country=my_country)
        all_matches.append(
            {
                "id": p.id,
                "platform": p.source,
                "company": p.company,
                "title": p.title,
                "location": p.location,
                "url": p.source_url,
                "eligibility_status": elig["status"],
                "eligibility_can_apply": elig["can_apply"]["verdict"] if elig["can_apply"] else None,
            }
        )

    print(f"✨ Found {len(all_matches)} matching opportunities:\n")

    for idx, j in enumerate(all_matches[: args.limit], 1):
        source = j.get("platform") or j.get("source", "Board")
        elig_tag = j["eligibility_status"]
        if j.get("eligibility_can_apply"):
            elig_tag += f" ({j['eligibility_can_apply']})"
        print(f"{idx}. [{source}] {j['title']} @ {j['company']}")
        print(f"   Location:    {j.get('location', 'Remote')}")
        print(f"   Eligibility: {elig_tag} [heuristic]")
        print(f"   Apply:       {j['url']}\n")

    if args.save and store is not None and stats is not None:
        print(
            f"💾 Saved to SQLite store '{store.db_path}': "
            f"inserted={stats['inserted']}, updated={stats['updated']}, closed={stats['closed']}."
        )
        if args.save != "__DB__":
            with open(args.save, "w", encoding="utf-8") as f:
                json.dump(all_matches, f, indent=2)
            print(f"💾 Results also exported to '{args.save}'.")


def cmd_match(args):
    """Computes keyword match and ATS skill gap against a job description."""
    profile = _load_profile_or_exit(args.profile)
    jd_content = ""
    if os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()
    else:
        jd_content = args.jd

    res = compute_ats_match(jd_content, profile)
    elig = check_eligibility(jd_content, my_country=getattr(args, "my_country", None))
    res["eligibility"] = elig

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
    print("-" * 60)
    print(f"Remote Eligibility:   {elig['status']} (heuristic)")
    if elig["regions"]:
        print(f"Detected Regions:     {', '.join(elig['regions'])}")
    if elig["can_apply"]:
        print(f"Can Apply ({elig['can_apply']['country']}):     {elig['can_apply']['verdict']}")
    for ev in elig["evidence"][:3]:
        print(f"  • [{ev['rule_id']}] \"{ev['snippet']}\"")
    print("=" * 60 + "\n")


def cmd_eligibility(args):
    """Inspects job description text for remote geo-eligibility restrictions."""
    jd_content = ""
    if os.path.exists(args.jd):
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_content = f.read()
    else:
        jd_content = args.jd

    elig = check_eligibility(jd_content, my_country=args.my_country)

    if getattr(args, "json", False):
        print(json.dumps(elig, indent=2))
        sys.exit(0)

    print("\n" + "=" * 64)
    print("🌍 Remote Geo-Eligibility Check (Heuristic)")
    print("=" * 64)
    print(f"Status:          {elig['status']}")
    print(f"Notice:          {elig['notice']}")
    if elig["regions"]:
        print(f"Regions/Flags:   {', '.join(elig['regions'])}")
    if elig["can_apply"]:
        print(f"Can Apply ({elig['can_apply']['country']}):  {elig['can_apply']['verdict']}")
    if elig["evidence"]:
        print("\nEvidence Snippets:")
        for ev in elig["evidence"]:
            print(f"  • [{ev['rule_id']} | {ev['region']} | {ev['severity']}] {ev['snippet']}")
    else:
        print("\nNo geographic or visa restriction patterns matched.")
    print("=" * 64 + "\n")


def cmd_tailor(args):
    """Tailors master profile bullets to match a job description and generates a 1-page CV."""
    profile = _load_profile_or_exit(args.profile)
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

    if getattr(args, "diff", False):
        from rich.table import Table

        console = _track_console()
        diff_table = Table(
            title="Bullet Selection Diff Breakdown",
            show_header=True,
            header_style="bold cyan",
        )
        diff_table.add_column("Status", width=10)
        diff_table.add_column("Role", width=22)
        diff_table.add_column("Total", justify="right", width=6)
        diff_table.add_column("Skill", justify="right", width=6)
        diff_table.add_column("Metric", justify="right", width=7)
        diff_table.add_column("Token", justify="right", width=6)
        diff_table.add_column("Wt", justify="right", width=5)
        diff_table.add_column("Bullet")

        for role_rep in report.get("roles_tailored", []):
            role_label = f"{role_rep.get('company', '')} ({role_rep.get('role', '')})"
            for bd in role_rep.get("bullet_diffs", []):
                status_str = "[bold green]SELECTED[/bold green]" if bd["selected"] else "[dim red]DROPPED[/dim red]"
                diff_table.add_row(
                    status_str,
                    role_label[:22],
                    str(bd["total_score"]),
                    str(bd["skill_score"]),
                    str(bd["metric_score"]),
                    str(bd["token_overlap_score"]),
                    str(bd["weight_score"]),
                    bd["text"],
                )
        console.print()
        console.print(diff_table)
        console.print()

    if getattr(args, "check", False):
        target_check_file = pdf_file if os.path.exists(pdf_file) else docx_file
        print(f"\n🩺 Running ATS parser fragility check on '{target_check_file}'...")
        _display_ats_sim_report(target_check_file, profile_path=args.profile)


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
    profile = _load_profile_or_exit(args.profile)
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

    if getattr(args, "check", False):
        target_check_file = pdf_file if os.path.exists(pdf_file) else docx_file
        print(f"\n🩺 Running ATS parser fragility check on '{target_check_file}'...")
        _display_ats_sim_report(target_check_file, profile_path=args.profile)


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


def _display_ats_sim_report(file_path: str, profile_path: str = None, as_json: bool = False) -> int:
    """Executes parser fragility check and prints rich diagnostics."""
    try:
        rep = run_ats_sim(file_path, profile_path=profile_path)
    except AtsSimFileError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if as_json:
        print(rep.model_dump_json(indent=2))
        return 0 if rep.score >= 80 else 1

    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(
            title=f"ATS Parser Fragility Diagnostic: {os.path.basename(file_path)}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Check ID", style="bold", width=18)
        table.add_column("Name", width=26)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Diagnostic Detail")

        for c in rep.checks:
            if c.passed:
                status = "[bold green]PASS[/bold green]"
            elif c.score >= 0.5:
                status = "[bold yellow]WARN[/bold yellow]"
            else:
                status = "[bold red]FAIL[/bold red]"
            table.add_row(c.id, c.name, status, c.detail)

        console.print()
        console.print(table)
        console.print()

        score_color = "green" if rep.score >= 80 else "red"
        status_text = "PASSED (ATS Parser Safe)" if rep.score >= 80 else "NEEDS ATTENTION"
        console.print(
            f"Overall Parseability Score: [bold {score_color}]{rep.score} / 100[/bold {score_color}] "
            f"— [bold {score_color}]{status_text}[/bold {score_color}]"
        )

        if rep.hard_caps_applied:
            for cap in rep.hard_caps_applied:
                console.print(f"  [bold yellow]⚠️ Hard Cap Applied:[/bold yellow] {cap}")

        if rep.failed_checks:
            console.print("\n[bold]Fix Recommendations:[/bold]")
            for c in rep.failed_checks:
                console.print(f"  • [bold cyan]{c.id}[/bold cyan]: {c.hint}")
        else:
            console.print("\n[bold green]🎉 Zero parser fragility issues detected! Clean document structure.[/bold green]")
        console.print()

    except ImportError:
        print("\n" + "=" * 70)
        print(f"ATS Parser Fragility Diagnostic: {os.path.basename(file_path)}")
        print("=" * 70)
        for c in rep.checks:
            status = "PASS" if c.passed else ("WARN" if c.score >= 0.5 else "FAIL")
            print(f"[{status:4s}] {c.id:18s} {c.name:24s} | {c.detail}")
        print("-" * 70)
        print(f"Overall Parseability Score: {rep.score} / 100 ({'PASSED' if rep.score >= 80 else 'NEEDS ATTENTION'})")
        if rep.hard_caps_applied:
            for cap in rep.hard_caps_applied:
                print(f"  * Hard Cap: {cap}")
        if rep.failed_checks:
            print("\nFix Recommendations:")
            for c in rep.failed_checks:
                print(f"  * [{c.id}]: {c.hint}")
        print("=" * 70 + "\n")

    return 0 if rep.score >= 80 else 1


def cmd_ats_sim(args):
    """Checks resume document for parser fragility flaws."""
    code = _display_ats_sim_report(
        args.file,
        profile_path=args.profile,
        as_json=getattr(args, "json", False),
    )
    sys.exit(code)


def _track_console():
    from rich.console import Console
    return Console()


def cmd_track_add(args):
    """Adds a job application from DB job ID, URL, or manual details."""
    store = CareerStore()
    jd_snapshot = None
    if getattr(args, "jd", None):
        if os.path.exists(args.jd):
            with open(args.jd, "r", encoding="utf-8") as f:
                jd_snapshot = f.read()
        else:
            jd_snapshot = args.jd

    company = getattr(args, "company", None)
    title = getattr(args, "title", None)
    if args.manual and (not company or not title):
        if sys.stdin.isatty():
            if not company:
                company = input("Company name: ").strip()
            if not title:
                title = input("Role title: ").strip()
        if not company or not title:
            print("Error: Manual entry requires --company and --title.", file=sys.stderr)
            sys.exit(2)

    try:
        app = store.add_application(
            job_id=args.job_id,
            url=args.url,
            manual=args.manual,
            company=company,
            title=title,
            location=args.location or "Remote",
            stage=args.stage,
            cv_path=args.cv,
            jd_snapshot=jd_snapshot,
            match_score=args.score,
            notes=args.notes or "",
            due_days=args.due_days,
        )
    except StoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(app, indent=2))
        sys.exit(0)

    print(f"✅ Tracked Application #{app['id']}: {app['title']} @ {app['company']} [{app['stage']}]")
    if app.get("cv_sha256"):
        print(f"   CV SHA-256: {app['cv_sha256']}")


def cmd_track_list(args):
    """Lists tracked job applications."""
    store = CareerStore()
    try:
        apps = store.list_applications(stage=args.stage)
    except StoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(apps, indent=2))
        sys.exit(0)

    if not apps:
        print("No tracked applications found. Run 'forge track add --help' to start tracking.")
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    table = Table(title="Tracked Job Applications", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="bold", width=5)
    table.add_column("Stage", width=11)
    table.add_column("Company", width=18)
    table.add_column("Title", width=26)
    table.add_column("Source", width=12)
    table.add_column("Applied", width=12)
    table.add_column("CV SHA", width=10)

    for a in apps:
        applied_str = (a.get("applied_at") or "-")[:10]
        cv_short = (a.get("cv_sha256") or "-")[:8]
        table.add_row(
            str(a["id"]),
            a["stage"],
            a.get("company", ""),
            a.get("title", ""),
            a.get("source", ""),
            applied_str,
            cv_short,
        )
    console.print()
    console.print(table)
    console.print()


def cmd_track_move(args):
    """Moves an application to another pipeline stage."""
    store = CareerStore()
    try:
        app_id = int(args.id)
        app = store.move_application(app_id, args.stage, note=args.note, due_days=args.due_days)
    except ValueError:
        print(f"Error: Invalid application ID '{args.id}'. Must be an integer.", file=sys.stderr)
        sys.exit(2)
    except StoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(app, indent=2))
        sys.exit(0)

    print(f"✅ Moved Application #{app['id']} ({app['company']} - {app['title']}) -> [{app['stage']}]")


def cmd_track_note(args):
    """Adds a note to an existing application."""
    store = CareerStore()
    try:
        app_id = int(args.id)
        app = store.add_note(app_id, args.text)
    except ValueError:
        print(f"Error: Invalid application ID '{args.id}'. Must be an integer.", file=sys.stderr)
        sys.exit(2)
    except StoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(app, indent=2))
        sys.exit(0)

    print(f"📝 Note saved to Application #{app['id']}.")


def cmd_track_show(args):
    """Displays full details and event timeline for an application."""
    store = CareerStore()
    try:
        app_id = int(args.id)
    except ValueError:
        print(f"Error: Invalid application ID '{args.id}'. Must be an integer.", file=sys.stderr)
        sys.exit(2)

    app = store.get_application(app_id)
    if app is None:
        print(f"Error: Application #{app_id} not found.", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(app, indent=2))
        sys.exit(0)

    print("\n" + "=" * 64)
    print(f"Application #{app['id']}: {app['title']} @ {app['company']}")
    print("=" * 64)
    print(f"Stage:        {app['stage']}")
    print(f"Source:       {app.get('source', '')} | Location: {app.get('location', '')}")
    print(f"URL:          {app.get('url') or '-'}")
    print(f"Applied At:   {app.get('applied_at') or '-'}")
    print(f"Next Action:  {app.get('next_action_at') or '-'}")
    print(f"CV Path:      {app.get('cv_path') or '-'}")
    print(f"CV SHA-256:   {app.get('cv_sha256') or '-'}")
    print(f"Match Score:  {app.get('match_score') if app.get('match_score') is not None else '-'}")
    print(f"Notes:        {app.get('notes') or '-'}")
    if app.get("jd_snapshot"):
        preview = app["jd_snapshot"].strip().replace("\n", " ")[:180]
        print(f"JD Snapshot:  {preview}...")
    print("-" * 64)
    print("Timeline Events:")
    for ev in app.get("events", []):
        print(f"  - [{ev['at']}] ({ev['kind']}) {ev['detail']}")
    print("=" * 64 + "\n")


def cmd_track_due(args):
    """Lists applications overdue for follow-up."""
    store = CareerStore()
    due_apps = store.get_due_applications(days=args.days)

    if getattr(args, "json", False):
        print(json.dumps(due_apps, indent=2))
        sys.exit(0)

    if not due_apps:
        print(f"✅ No applications due for follow-up (>= {args.days} days).")
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    table = Table(title=f"Follow-Ups Due (>= {args.days} days)", show_header=True, header_style="bold yellow")
    table.add_column("ID", style="bold", width=5)
    table.add_column("Stage", width=11)
    table.add_column("Company", width=18)
    table.add_column("Title", width=26)
    table.add_column("Days Elapsed", justify="right", width=12)

    for a in due_apps:
        table.add_row(
            str(a["id"]),
            a["stage"],
            a.get("company", ""),
            a.get("title", ""),
            str(a.get("days_since_applied", 0)),
        )
    console.print()
    console.print(table)
    console.print("\nTip: Draft a follow-up note with 'forge track note <id> \"Sent follow-up\"'.\n")


def cmd_track_ghosted(args):
    """Suggests stagnant applications that may be ghosted without auto-moving."""
    store = CareerStore()
    candidates = store.get_ghost_candidates(days=args.days)

    if getattr(args, "json", False):
        print(json.dumps(candidates, indent=2))
        sys.exit(0)

    if not candidates:
        print(f"✅ No applications stagnant for >= {args.days} days.")
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    table = Table(
        title=f"Suggested Ghosted Candidates (>= {args.days} days inactive; not auto-moved)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("ID", style="bold", width=5)
    table.add_column("Stage", width=11)
    table.add_column("Company", width=18)
    table.add_column("Title", width=26)
    table.add_column("Days Inactive", justify="right", width=14)

    for a in candidates:
        table.add_row(
            str(a["id"]),
            a["stage"],
            a.get("company", ""),
            a.get("title", ""),
            str(a.get("stale_days", 0)),
        )
    console.print()
    console.print(table)
    console.print("\nTo mark any item ghosted manually, run: forge track move <id> ghosted\n")


def cmd_track_export(args):
    """Exports tracked applications as CSV or Markdown."""
    if not args.csv and not args.md:
        print("Error: Specify either --csv or --md for export format.", file=sys.stderr)
        sys.exit(2)
    if args.csv and args.md:
        print("Error: Choose only one of --csv or --md.", file=sys.stderr)
        sys.exit(2)

    fmt = "csv" if args.csv else "md"
    store = CareerStore()
    output_text = store.export_applications(fmt=fmt)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"💾 Exported {fmt.upper()} report to '{args.out}'.")
    else:
        print(output_text, end="")


def cmd_track_board(args):
    """Launches the optional Textual Kanban TUI board."""
    try:
        from careerforge.tui import run_board_tui
    except ImportError:
        print(
            "Error: Terminal UI requires optional [tui] extra. Install with: pip install careerforge[tui]",
            file=sys.stderr,
        )
        sys.exit(2)

    run_board_tui()


def cmd_report(args):
    """Generates application funnel, CV response rates, and timing metrics."""
    store = CareerStore()
    try:
        rep = generate_report(store, since=args.since)
    except ReportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(rep, indent=2))
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    console.print()
    title_suffix = f" (since {args.since})" if args.since else ""
    table = Table(
        title=f"Application Funnel Report{title_suffix}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Stage", style="bold", width=12)
    table.add_column("Count", justify="right", width=7)
    table.add_column("Step %", justify="right", width=9)
    table.add_column("Bar", width=22)

    max_count = max((s["count"] for s in rep["funnel"]), default=1) or 1
    for step in rep["funnel"]:
        bar_len = int(round((step["count"] / max_count) * 20))
        bar = "█" * bar_len + "░" * (20 - bar_len)
        table.add_row(
            step["stage"],
            str(step["count"]),
            f"{step['step_conversion_pct']}%",
            bar,
        )

    console.print(table)
    console.print(f"Funnel Sparkline: [bold cyan]{rep['funnel_sparkline']}[/bold cyan]")
    if rep["avg_response_days"] is not None:
        console.print(f"Average Days to First Response: {rep['avg_response_days']} days")
    if rep["avg_active_days"] is not None:
        console.print(f"Average Active Application Age: {rep['avg_active_days']} days")

    if rep["by_cv_version"]:
        cv_table = Table(title="Response Rate by CV Version (SHA-256)", show_header=True, header_style="bold green")
        cv_table.add_column("CV Hash", width=14)
        cv_table.add_column("Applied", justify="right", width=9)
        cv_table.add_column("Responded", justify="right", width=10)
        cv_table.add_column("Rate", justify="right", width=8)
        for row in rep["by_cv_version"]:
            cv_table.add_row(
                row["cv_hash"],
                str(row["applied"]),
                str(row["responded"]),
                f"{row['response_rate_pct']}%",
            )
        console.print()
        console.print(cv_table)

    if rep["by_source"]:
        src_table = Table(title="Response Rate by Source", show_header=True, header_style="bold blue")
        src_table.add_column("Source", width=16)
        src_table.add_column("Applied", justify="right", width=9)
        src_table.add_column("Responded", justify="right", width=10)
        src_table.add_column("Rate", justify="right", width=8)
        for row in rep["by_source"]:
            src_table.add_row(
                row["source"],
                str(row["applied"]),
                str(row["responded"]),
                f"{row['response_rate_pct']}%",
            )
        console.print()
        console.print(src_table)

    for w in rep["warnings"]:
        console.print(f"[bold yellow]Warning:[/bold yellow] {w}")
    console.print()


def cmd_ghost(args):
    """Evaluates heuristic Ghost Risk on stored job listings."""
    if args.top <= 0:
        print("Error: --top must be a positive integer.", file=sys.stderr)
        sys.exit(2)

    store = CareerStore()
    try:
        res = analyze_ghost_jobs(store, job_id=args.job_id, top=args.top)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    console.print(f"\n[bold yellow]Notice:[/bold yellow] {res['notice']}\n")

    if not res["items"]:
        print("No jobs in local database yet. Run 'forge scrape --save' or 'forge track add' first.")
        sys.exit(0)

    table = Table(title="Ghost Risk Heuristic Audit", show_header=True, header_style="bold cyan")
    table.add_column("ID", width=5)
    table.add_column("Risk", width=8)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Company", width=16)
    table.add_column("Title", width=24)
    table.add_column("Reasons")

    for item in res["items"]:
        lvl = item["risk_level"]
        lvl_styled = (
            "[bold red]High[/bold red]"
            if lvl == "High"
            else ("[bold yellow]Medium[/bold yellow]" if lvl == "Medium" else "[bold green]Low[/bold green]")
        )
        table.add_row(
            str(item["job_id"]),
            lvl_styled,
            str(item["risk_score"]),
            item["company"],
            item["title"],
            "; ".join(item["reasons"]),
        )
    console.print(table)
    console.print()


def cmd_salary(args):
    """Computes heuristic salary percentiles strictly from stored listings."""
    store = CareerStore()
    try:
        res = analyze_salaries(
            store,
            role=args.role,
            keyword=args.keyword,
            currency=args.currency,
            rates_path=args.rates,
        )
    except SalaryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2))
        sys.exit(0)

    from rich.table import Table

    console = _track_console()
    console.print(f"\n[bold yellow]Notice:[/bold yellow] {res['notice']}\n")

    if res["buckets"]:
        table = Table(title="Disclosed Compensation Bands", show_header=True, header_style="bold cyan")
        table.add_column("Currency", width=9)
        table.add_column("Count", justify="right", width=6)
        table.add_column("Min", justify="right", width=11)
        table.add_column("P25", justify="right", width=11)
        table.add_column("Median", justify="right", width=11)
        table.add_column("P75", justify="right", width=11)
        table.add_column("Max", justify="right", width=11)

        for b in res["buckets"]:
            table.add_row(
                b["currency"],
                str(b["count"]),
                f"{b['min']:,.0f}",
                f"{b['p25']:,.0f}",
                f"{b['median']:,.0f}",
                f"{b['p75']:,.0f}",
                f"{b['max']:,.0f}",
            )
        console.print(table)
        console.print()

    for w in res["warnings"]:
        console.print(f"[bold yellow]Warning:[/bold yellow] {w}")
    console.print()


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
    p_scrape.add_argument(
        "--my-country",
        type=str,
        default=None,
        help="Your country code (e.g. BD, US) for heuristic remote geo-eligibility hints",
    )
    p_scrape.add_argument(
        "--save",
        nargs="?",
        const="__DB__",
        default=None,
        help="Save results to local SQLite DB (default with --save) or specify JSON export path",
    )
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
    p_apply.add_argument(
        "--check",
        action="store_true",
        help="Automatically run ATS parser fragility check on generated PDF",
    )
    p_apply.set_defaults(func=cmd_apply)

    # ats-sim
    p_ats = subparsers.add_parser(
        "ats-sim",
        help="Inspect resume for parser fragility flaws (formatting, fonts, columns, encodings)",
    )
    p_ats.add_argument("file", type=str, help="Path to resume file (.pdf or .docx)")
    p_ats.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Path to candidate profile.yaml for field recovery check",
    )
    p_ats.add_argument("--json", action="store_true", help="Output diagnostic report as JSON")
    p_ats.set_defaults(func=cmd_ats_sim)

    # audit
    p_audit = subparsers.add_parser("audit", help="Audit a text file against Anti-AI standards")
    p_audit.add_argument("--file", type=str, required=True, help="Path to text or markdown file")
    p_audit.add_argument("--json", action="store_true", help="Output audit report as JSON")
    p_audit.set_defaults(func=cmd_audit)

    # match
    p_match = subparsers.add_parser("match", help="Analyze ATS keyword gap against a job description")
    p_match.add_argument("--jd", type=str, required=True, help="Path to job description file or raw text string")
    p_match.add_argument("--profile", type=str, default=None, help="Path to profile.yaml")
    p_match.add_argument("--my-country", type=str, default=None, help="Country code (e.g. BD, US) for geo-eligibility check")
    p_match.add_argument("--json", action="store_true", help="Output match report as JSON")
    p_match.set_defaults(func=cmd_match)

    # eligibility
    p_elig = subparsers.add_parser("eligibility", help="Check job description text for remote geo-restrictions (heuristic)")
    p_elig.add_argument("--jd", type=str, required=True, help="Path to job description file or raw text string")
    p_elig.add_argument("--my-country", type=str, default=None, help="Country code (e.g. BD, US) for application verdict")
    p_elig.add_argument("--json", action="store_true", help="Output eligibility report as JSON")
    p_elig.set_defaults(func=cmd_eligibility)

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
    p_tailor.add_argument(
        "--check",
        action="store_true",
        help="Automatically run ATS parser fragility check on generated PDF",
    )
    p_tailor.add_argument(
        "--diff",
        action="store_true",
        help="Show score breakdown explaining why each bullet was selected or dropped",
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

    # track
    p_track = subparsers.add_parser("track", help="Track job applications locally in SQLite")
    track_sub = p_track.add_subparsers(dest="track_action", help="Tracking actions")

    p_t_add = track_sub.add_parser("add", help="Add an application from job ID, URL, or manual input")
    p_t_add.add_argument("job_id", nargs="?", default=None, help="Existing job ID or external_id from scraped jobs")
    p_t_add.add_argument("--url", type=str, default=None, help="Job posting URL")
    p_t_add.add_argument("--manual", action="store_true", help="Create job entry manually")
    p_t_add.add_argument("--company", type=str, default=None, help="Company name")
    p_t_add.add_argument("--title", type=str, default=None, help="Role title")
    p_t_add.add_argument("--location", type=str, default="Remote", help="Job location (default: Remote)")
    p_t_add.add_argument("--stage", choices=list(VALID_STAGES), default="saved", help="Initial stage (default: saved)")
    p_t_add.add_argument("--cv", type=str, default=None, help="Path to submitted CV file (records path and SHA-256)")
    p_t_add.add_argument("--jd", type=str, default=None, help="JD file path or raw text to snapshot")
    p_t_add.add_argument("--score", type=float, default=None, help="ATS match score snapshot")
    p_t_add.add_argument("--notes", type=str, default="", help="Initial notes")
    p_t_add.add_argument("--due-days", type=int, default=7, help="Follow-up cadence in days when applied (default: 7)")
    p_t_add.add_argument("--json", action="store_true", help="Output JSON")
    p_t_add.set_defaults(func=cmd_track_add)

    p_t_list = track_sub.add_parser("list", help="List tracked applications")
    p_t_list.add_argument("--stage", type=str, default=None, help="Filter by stage")
    p_t_list.add_argument("--json", action="store_true", help="Output JSON")
    p_t_list.set_defaults(func=cmd_track_list)

    p_t_move = track_sub.add_parser("move", help="Move an application to another stage")
    p_t_move.add_argument("id", type=str, help="Application ID")
    p_t_move.add_argument("stage", type=str, help=f"Target stage ({', '.join(VALID_STAGES)})")
    p_t_move.add_argument("--note", type=str, default=None, help="Optional event note")
    p_t_move.add_argument("--due-days", type=int, default=7, help="Follow-up window in days (default: 7)")
    p_t_move.add_argument("--json", action="store_true", help="Output JSON")
    p_t_move.set_defaults(func=cmd_track_move)

    p_t_note = track_sub.add_parser("note", help="Append a timestamped note to an application")
    p_t_note.add_argument("id", type=str, help="Application ID")
    p_t_note.add_argument("text", type=str, help="Note text")
    p_t_note.add_argument("--json", action="store_true", help="Output JSON")
    p_t_note.set_defaults(func=cmd_track_note)

    p_t_show = track_sub.add_parser("show", help="Show application details and event history")
    p_t_show.add_argument("id", type=str, help="Application ID")
    p_t_show.add_argument("--json", action="store_true", help="Output JSON")
    p_t_show.set_defaults(func=cmd_track_show)

    p_t_due = track_sub.add_parser("due", help="List applications needing follow-up")
    p_t_due.add_argument("--days", type=int, default=7, help="Days since applied threshold (default: 7)")
    p_t_due.add_argument("--json", action="store_true", help="Output JSON")
    p_t_due.set_defaults(func=cmd_track_due)

    p_t_ghost = track_sub.add_parser("ghosted", help="Suggest stale applications that may be ghosted")
    p_t_ghost.add_argument("--days", type=int, default=21, help="Days inactive threshold (default: 21)")
    p_t_ghost.add_argument("--json", action="store_true", help="Output JSON")
    p_t_ghost.set_defaults(func=cmd_track_ghosted)

    p_t_export = track_sub.add_parser("export", help="Export applications as CSV or Markdown")
    p_t_export.add_argument("--csv", action="store_true", help="Export as CSV")
    p_t_export.add_argument("--md", action="store_true", help="Export as Markdown table")
    p_t_export.add_argument("--out", type=str, default=None, help="Output file path (prints to stdout if omitted)")
    p_t_export.set_defaults(func=cmd_track_export)

    p_t_board = track_sub.add_parser("board", help="Launch interactive Kanban TUI (requires careerforge[tui])")
    p_t_board.set_defaults(func=cmd_track_board)

    # report
    p_report = subparsers.add_parser("report", help="Show application funnel and response rate analytics")
    p_report.add_argument("--since", type=str, default=None, help="Filter window: YYYY-MM-DD or Nd (e.g. 30d)")
    p_report.add_argument("--json", action="store_true", help="Output JSON report")
    p_report.set_defaults(func=cmd_report)

    # ghost
    p_ghost = subparsers.add_parser("ghost", help="Evaluate heuristic Ghost Risk scores on stored jobs")
    p_ghost.add_argument("job_id", nargs="?", default=None, help="Optional job ID or external_id to inspect")
    p_ghost.add_argument("--top", type=int, default=20, help="Show top N highest-risk jobs (default: 20)")
    p_ghost.add_argument("--json", action="store_true", help="Output JSON report")
    p_ghost.set_defaults(func=cmd_ghost)

    # salary
    p_salary = subparsers.add_parser("salary", help="Analyze salary percentiles from disclosed job postings")
    p_salary.add_argument("--role", type=str, default=None, help="Filter postings by role title/text")
    p_salary.add_argument("--keyword", type=str, default=None, help="Additional keyword filter")
    p_salary.add_argument("--currency", type=str, default=None, help="Target or filter currency code (e.g. USD)")
    p_salary.add_argument("--rates", type=str, default=None, help="Path to user-supplied currency rates YAML")
    p_salary.add_argument("--json", action="store_true", help="Output JSON report")
    p_salary.set_defaults(func=cmd_salary)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    if args.command == "track" and not getattr(args, "track_action", None):
        p_track.print_help()
        sys.exit(2)

    args.func(args)


if __name__ == "__main__":
    main()
