# Interview & STAR Story Preparation (`forge interview`)

`forge interview` helps you prepare behavioral interview stories grounded strictly in your real work history without fabricated anecdotes or cloud AI calls. Everything runs locally on your machine using `profile.yaml`, curated YAML question banks, and a local `stories.yaml` story bank.

## Commands

| Command | Purpose |
|---|---|
| `forge interview draft` | Extract metric-bearing bullets and projects from `profile.yaml` into STAR outlines (`TODO: fill in` for unstated parts) |
| `forge interview add` | Add a STAR story to `stories.yaml` |
| `forge interview list` | List saved STAR stories, optionally filtered by `--tag` |
| `forge interview edit <id>` | Update fields or category tags on an existing story |
| `forge interview coverage` | Audit coverage across 8 standard behavioral categories (`0 stories` gaps highlighted) |
| `forge interview practice` | Pick curated role questions (`general`, `data`, `backend`, `frontend`) with `--seed`, optional `--timer`, and `--audit` |

## Honesty Design

CareerForge never invents managers, blockers, or outcomes that are not in your profile:

1. `Situation` pulls only your verified role title, company name, duration, and location (or project title and stack).
2. `Task` always starts as `TODO: fill in`, prompting you to supply the real problem or constraint you faced.
3. `Action` copies your verbatim profile bullet or project description without inflating it.
4. `Result` keeps `TODO: fill in` so you record exact verified impact, citing any numeric metrics already found in `profile.yaml`.

## Examples

```bash
# Draft STAR outlines from your profile and save them
forge interview draft --profile examples/profile.example.yaml --save

# Check which behavioral categories still have 0 stories
forge interview coverage

# Practice a deterministic data analyst question and audit your answer for AI clichés
forge interview practice --role data --seed 42 --timer 90 --answer-file answer.txt --audit
```

## Story Bank Storage

By default, `stories.yaml` lives in your OS user data directory via `platformdirs` (`user_data_dir("careerforge")`). Override the location using `--stories <path>`, `CAREERFORGE_STORIES`, or `CAREERFORGE_DATA_DIR`.

## Limitations

* Question banks are static curated prompts per track (`general`, `data`, `backend`, `frontend`), not adaptive follow-up interviewers.
* `forge interview draft` cannot extract narrative context that was omitted from `profile.yaml`; unstated STAR sections remain `TODO: fill in` until you fill them in.
* The `--audit` flag uses `forge audit` regex and cadence heuristics and does not evaluate technical correctness or domain depth.
* Live interactive typing prompt reads stdin line-by-line; automated scripts should pass `--answer`, `--answer-file`, or `--story-id`.
