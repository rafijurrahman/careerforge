# Heuristic Ghost Job Detector (`forge ghost`)

> **Important Notice:** `forge ghost` outputs a **heuristic risk estimate, not proof** of whether an employer is actively hiring. Legitimate teams sometimes leave evergreen roles open for months.

`forge ghost` runs offline against the `jobs` table in your local SQLite store (`careerforge.db`). It inspects five signals to classify postings into `Low` (< 30), `Medium` (30 to 59), or `High` (>= 60) risk.

## Signal Weights

| Signal | Max Points | Trigger Conditions |
|---|---:|---|
| `AGE` | 25 | Posting age >= 60 days (+25) or >= 30 days (+15), measured from `posted_at` (fallback: `first_seen`). |
| `REPOST` | 25 | Same normalized `(company, title)` appears >= 3 times (+25) or 2 times (+15) in the local DB. |
| `STALE_OR_CLOSED` | 20 | `closed_at` already recorded (+20), or an open posting was not seen in scrapes for >= 14 days (+10). |
| `VAGUE_JD` | 15 | Missing salary fields AND empty/short description < 120 chars (+15), or missing clear requirement/responsibility terms (+8). |
| `UNCHANGED_HASH` | 15 | `description_hash` remained identical across >= 30 days (+15) or >= 14 days (+8) between `description_changed_at` and `last_seen`. |

## CLI Usage
- Inspect top risky postings: `forge ghost --top 20`
- Inspect a single stored job: `forge ghost <job-id>`
- Machine-readable output: `forge ghost --json`

## Limitations
1. A high score reflects structural staleness or sparse job text, not confirmed hiring freezes.
2. Evergreen pipelines (large tech firms hiring continuously into general pools) often trigger `AGE` and `UNCHANGED_HASH` even when actively interviewing.
3. Accuracy depends on running `forge scrape --save` regularly over time so `first_seen`, `last_seen`, and `description_hash` history exist locally.
