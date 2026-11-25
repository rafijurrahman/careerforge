# Offline Salary Band Analyzer (`forge salary`)

> **Notice:** `forge salary` produces **heuristic compensation estimates** computed strictly from job postings stored in your local SQLite database (`jobs` table). It applies **zero cost-of-living adjustments** and uses **zero hardcoded or online exchange rates**.

## Methodology
1. Selects stored postings where `salary_min` or `salary_max` is present.
2. Filters optionally by `--role` and `--keyword` across job titles and descriptions.
3. Computes each posting's salary midpoint `(salary_min + salary_max) / 2` (or single reported bound) and calculates `min`, `p25`, `median` (`p50`), `p75`, and `max` per currency.
4. Currency conversion occurs **only** if you pass `--rates path/to/rates.yaml`. Unmapped currencies are skipped and counted explicitly in warnings.

### Example `rates.yaml`
```yaml
base: USD
rates:
  USD: 1.0
  EUR: 1.10
  GBP: 1.27
```
*(Multiplier converts currency -> base: `amount * rate = base_amount`.)*

## Mandatory Statistical Warnings
- **Selection Bias:** Employers that disclose compensation differ systematically from employers that hide pay ranges. Results represent only disclosed postings.
- **Small Sample Warning (`n < 10`):** When fewer than 10 disclosed postings match your filters, CareerForge prints a small-sample warning because percentiles become unstable.

## Limitations
1. ATS APIs report structured salary fields unevenly; postings that hide pay inside plain text descriptions without numeric schema fields are omitted.
2. Currencies are never inferred if missing (`UNKNOWN` bucket) and never adjusted for regional purchasing power or taxes.
3. Offline-only: exchange rates must come from your local YAML file when combining currencies.
