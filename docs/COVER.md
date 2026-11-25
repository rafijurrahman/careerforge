# Template Outreach & Cover Drafts (`forge cover`)

`forge cover` builds concise application messages locally from plain-text templates (`hook -> proof -> ask`) and your verified achievements in `profile.yaml`. Every template avoids LLM calls, avoids cloud uploads, inserts `<<FILL: ...>>` markers for missing context, and runs the local `forge audit` engine on every generated draft.

## Supported Types

| Type (`--type`) | Structure & Target Length | When to Use |
|---|---|---|
| `cover` | `hook -> proof -> ask`, strictly capped at 200 words (target 150-200) | Short application cover note |
| `cold-email` | Subject line + concise note (under 115 words) | Reaching out directly to engineering managers or founders |
| `linkedin` | Connection-length message (under 300 characters / 80 words) | Short LinkedIn invite or InMail opener |
| `follow-up` | Application follow-up referencing applied date (`--app <id>`) | Checking in when `forge track due` flags an overdue application |

## Examples

```bash
# Draft a 150-200 word cover letter for a JD
forge cover --jd jd.txt --company "Acme Labs" --role "Data Analyst"

# Draft a follow-up from an application tracked in SQLite
forge cover --type follow-up --app 3

# Draft a LinkedIn connection note and write to file
forge cover --jd jd.txt --type linkedin --company "Northwind" --role "Backend Engineer" --out note.txt
```

## Honesty & Fill Markers

When hiring manager names, company names, role titles, or application dates are absent from your flags, tracked record, or explicit `Company:` / `Role:` headers in the JD, CareerForge emits explicit `<<FILL: ...>>` markers instead of guessing names or salutation defaults.

## Limitations

* `forge cover` uses static plain-text templates (`careerforge/data/templates/`), not generative prose or company news lookups.
* If your `profile.yaml` contains long bullets, CareerForge trims extra clauses on word boundaries to stay within strict length caps; always read and personalize `<<FILL: ...>>` markers before sending.
* Automatic `forge audit` checks stylistic markers and cadence; it cannot verify company fit or grammar across manual edits you make afterward.
