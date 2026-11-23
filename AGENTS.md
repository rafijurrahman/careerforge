# AGENTS.md — AI Tool Compatibility

CareerForge works alongside any local AI coding tool. Here is what each tool can do with this codebase.

---

## Google Antigravity (Gemini)

Compatible. Antigravity can:
- Run `python cli.py setup` via terminal
- Read and edit `profile.yaml` directly
- Generate tailored bullet points for a specific job description
- Run `python cli.py audit --file <text>` and interpret the report
- Scrape and filter job results with `python cli.py scrape`

Recommended use: paste the job description into the chat and ask Antigravity to tailor your profile bullets before running `apply`.

---

## Claude Code (Anthropic)

Compatible. Claude Code can:
- Read all source files via its file tools
- Edit `profile.yaml` to tailor bullet points
- Run CLI commands via bash tool
- Extend scrapers by writing new scanner files

Recommended: add an `CLAUDE.md` file at the repo root with your usage context if you use Claude Code regularly.

---

## GitHub Copilot / Cursor / Codex

Compatible for code editing and autocomplete. These tools work well for:
- Extending `board_registry.py` with new company slugs
- Writing additional scanner modules
- Editing `cv_builder.py` templates

They do not run CLI commands directly — use the terminal for that.

---

## Running CareerForge With an AI Assistant

A good workflow:

1. Open the job posting in your browser
2. Copy the full job description text
3. Tell your AI assistant: "Here is a job description. Update my profile bullets to match and run `python cli.py apply --role-tag JobTitle`."
4. The assistant edits `profile.yaml` and runs the command
5. Output CV is in `output/`

---

## What to Keep Private

Your `profile.yaml` contains personal information. It is in `.gitignore` and should not be shared with any cloud-based AI tool unless you are comfortable with that. Use local-only AI tools (like a local Ollama model or Antigravity running locally) if privacy is a concern.
