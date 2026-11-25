# Heuristic Remote Geo-Eligibility Checker (`forge eligibility` / `match` / `scrape`)

> **Scope Notice:** Geo-eligibility outputs are **heuristic pattern matches**, not legal immigration or employer policy guarantees. Always verify work authorization and location clauses in the original job posting.

Many job listings claim "Remote" or "Worldwide" in headers while embedding US citizenship, timezone overlap, or no-sponsorship restrictions deeper in the description.

## Rule Architecture
Rules live in [`careerforge/data/eligibility_rules.yaml`](../careerforge/data/eligibility_rules.yaml), each defining:
- `id`: Stable identifier (`ELIG-US-01`, `ELIG-VISA-01`, `ELIG-TZ-AMERICAS`, `ELIG-EU-01`, `ELIG-UK-01`, etc.)
- `regex`: Case-insensitive matching pattern
- `region`: Normalized region/constraint tag (`US`, `EU`, `UK`, `CA`, `VISA_RESTRICTED`, `AMERICAS_TZ`)
- `severity`: `restricted` or `likely_restricted`
- `notes`: Plain-language explanation

### False-Positive Reduction & Precedence
1. **Sentence-Level Negative Guards:** Office location statements such as *"Our team is located in San Francisco"* or *"Headquarters in London"* are ignored unless the same sentence also contains obligation terms (`must`, `required`, `only`, `authorized`, `citizens`, `sponsorship`).
2. **Restriction Precedence:** If a listing mentions both `"Worldwide"` / `"Anywhere"` and an explicit geo or visa restriction sentence, the restriction overrides generic remote labels.
3. **Applicant Verdict (`--my-country`):** Passing `--my-country BD` (or `US`, `UK`, `DE`, etc.) checks detected regional restrictions against your country and outputs a heuristic verdict (`Yes`, `No`, or `Check JD`) with supporting evidence snippets.

## CLI Usage
- Standalone check: `forge eligibility --jd job.txt --my-country BD [--json]`
- Integrated keyword + eligibility match: `forge match --jd job.txt --my-country BD`
- Integrated scraper annotation: `forge scrape --roles "Data Analyst" --my-country BD`

## Limitations
1. Regex rules catch explicit English phrasing; restrictions phrased idiomatically or embedded in external application forms cannot be detected from plain text alone.
2. Timezone overlap flags (`Likely restricted`) warn about working hours rather than legal residency; some candidates choose to work overlapping hours across timezones.
3. Regional country alias mappings cover major regions (`US`, `UK`, `CA`, `EU`, `BD`, `IN`, `AU`, `LATAM`) and fall back to uppercase country codes otherwise.
