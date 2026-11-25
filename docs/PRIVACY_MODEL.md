# CareerForge Privacy Model

CareerForge is designed from the ground up to be **100% offline-first and private**. Your career history, contact details, applications, and salary targets belong exclusively to you.

---

## 🔒 Privacy Guarantees

| Guarantee | How It Is Enforced |
|---|---|
| **Zero Telemetry** | No analytics, no tracking pixels, no event logging sent to external servers. |
| **Local-Only Profiles** | `profile.yaml` is stored on your disk and strictly `.gitignore`d. |
| **Zero Account Signups** | No passwords, no logins, no authentication tokens needed for core features. |
| **No Cloud LLM Leaks** | Anti-AI auditing and keyword matching run locally on your CPU via deterministic algorithms. |
| **Isolated Scrapers** | Scrapers fetch only public, unauthenticated job boards (Greenhouse, Ashby, Remotive) using standard HTTPS GET. |

---

## 🌐 Network Activity Audit

| Command | Uses Network? | External Domains Contacted | Notes |
|---|:---:|---|---|
| `forge init` | ❌ No | None | Runs locally |
| `forge doctor` | ❌ No | None | Inspects local system environment |
| `forge ats-sim` | ❌ No | None | Inspects local PDF/DOCX for parser fragility and encoding flaws |
| `forge tailor` | ❌ No | None | Re-ranks profile bullets locally using offline knapsack algorithm |
| `forge apply` | ❌ No | None | Generates DOCX/PDF via local Word COM / LibreOffice |
| `forge audit` | ❌ No | None | Scans text locally using regex and linguistic rules |
| `forge match` | ❌ No | None | Compares text against local `skills.yaml` and `eligibility_rules.yaml` |
| `forge eligibility` | ❌ No | None | Evaluates geo-restriction rules strictly offline |
| `forge dorks` | ❌ No | None | Generates targeted Google search queries locally |
| `forge track` | ❌ No | None | Reads/writes strictly to local SQLite database (`careerforge.db`) |
| `forge report` | ❌ No | None | Computes funnel conversion metrics locally from SQLite |
| `forge ghost` | ❌ No | None | Scores heuristic Ghost Risk locally from stored SQLite jobs |
| `forge salary` | ❌ No | None | Aggregates salary percentiles locally; uses optional local `rates.yaml` only |
| `forge scrape` | ✅ Yes | `boards-api.greenhouse.io`, `api.ashbyhq.com`, `api.lever.co`, `remotive.com` | Fetches public job postings only. `--save` stores postings in local SQLite. Never transmits your profile. |

---

## 🛡️ Verifying Privacy Yourself

You can verify that CareerForge does not communicate externally during CV generation and auditing:

### On Windows (PowerShell):
```powershell
# Run apply with no network connection
Disable-NetAdapter -Name "Wi-Fi" -Confirm:$false
python cli.py apply
Enable-NetAdapter -Name "Wi-Fi" -Confirm:$false
```

### On Linux / macOS:
```bash
# Block all outgoing sockets during execution
unshare -n python cli.py apply
```

CareerForge runs without requiring an internet connection for all profile, CV tailoring, and auditing tasks.
