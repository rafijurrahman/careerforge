# ATS Parser Fragility Checker (`forge ats-sim`)

## 1. Overview and Core Philosophy

`forge ats-sim` is an offline **parser fragility checker** for resume documents (`.pdf` and `.docx`).

> **Important Scope Note:**
> `forge ats-sim` does **not** simulate Workday, Taleo, Greenhouse, or any specific applicant tracking system. No vendor publishes their proprietary ingestion algorithms, and actual parsing behaviors vary widely by client configuration. Instead, `forge ats-sim` inspects resumes for known structural, typographic, encoding, and layout patterns that break common document extractors, OCR pipelines, and text parsers.

### Core Principles
- **100% Offline & Private:** No network requests, no external API calls, and zero telemetry. All checks run locally on the user's machine.
- **Parser Fragility Focus:** Validates standard stream extraction, layout predictability, font embedding, Unicode sanitization, and section discoverability.
- **Actionable Diagnostics:** Every failing check yields a concrete, non-speculative fix hint.

---

## 2. Check Catalog

The tool runs up to 13 checks across the input document.

| Check ID | Name | Weight | Scope | What It Detects | Rationale | Fix Hint |
|---|---|---|---|---|---|---|
| `TEXT_EXTRACT` | Text Extraction | 15 | PDF & DOCX | Empty or near-empty text streams (< 50 characters). | Scanned image-only PDFs or corrupted stream encodings fail basic tokenization. | Export as a text-based PDF from Word or LibreOffice; avoid image-only scans. |
| `SECTIONS` | Standard Section Headings | 10 | PDF & DOCX | Presence of standard section headers (Experience, Education, Skills, Summary) or recognized aliases. | Parsers use standard headings to split text into discrete semantic blocks. Unusual labels lead to dropped sections. | Use conventional section headings like "Professional Experience", "Education", and "Skills". |
| `CONTACT` | Essential Contact Details | 10 | PDF & DOCX | Valid email address, telephone number, and professional link (LinkedIn / GitHub). | Missing or garbled contact details prevent candidate profile creation and recruiter contact. | Add a clearly formatted email, phone number, and LinkedIn URL in the body text. |
| `COLUMNS` | Multi-Column Layout | 10 | PDF & DOCX | Multi-column text flow. In PDF: horizontal cluster analysis across shared vertical spans. In DOCX: `w:cols` with count > 1. | Naive parsers read across columns horizontally, interleaving parallel columns into unreadable text. | Use a clean, single-column linear layout without side-by-side columns. |
| `DOCX_STRUCT` | DOCX Document Structure | 5 | DOCX | Tables (`w:tbl`), floating text boxes (`w:txbxContent`), and column sections. | Floating frames, text boxes, and nested tables are frequently ignored or parsed out of order. | Remove text boxes and tables; use standard left-aligned paragraphs with tabs or margins. |
| `HEADER_FOOTER` | Header & Footer Content | 5 | PDF & DOCX | Contact details trapped exclusively within page headers or footers (or top/bottom 5% margin zones in PDF). | Many parsers discard header and footer regions to eliminate page numbering noise, dropping contact information. | Move all contact details and critical content into the document body. |
| `UNICODE` | Unicode & Ligature Sanitization | 5 | PDF & DOCX | Typographic ligatures (U+FB00–U+FB06), zero-width characters (U+200B, U+FEFF), and non-standard quotes/dashes. | Ligatures (such as "fi" or "fl") extract as broken characters or blanks, breaking search queries like "Financial". | Replace ligatures with separate standard characters and strip zero-width spaces. |
| `ICON_GLYPHS` | Private Use Area Glyphs | 5 | PDF & DOCX | Unicode Private Use Area characters (U+E000–U+F8FF) typically inserted by icon fonts (FontAwesome). | Icon fonts map decorative symbols into private code points that render as replacement boxes or garbled text. | Remove icon fonts; use plain text labels (e.g., "Email:" or "Phone:") instead of icon glyphs. |
| `FONTS` | Font Embedding & Compatibility | 5 | PDF | Non-embedded fonts or non-standard font families outside common ATS-safe families (Calibri, Arial, Helvetica, Times, Georgia, Garamond). | Missing embedded fonts cause substitution shifts and broken character widths on server-side converters. | Embed fonts during PDF export and stick to standard system typography like Calibri or Arial. |
| `DATES` | Date Format Consistency | 5 | PDF & DOCX | Inconsistent date formatting (e.g., mixing "Jan 2024" with "01/2024" or irregular separators). | Irregular date patterns prevent chronological timeline parsers from calculating work tenure accurately. | Standardize dates across all roles (e.g., consistently use "MMM YYYY" or "MM/YYYY"). |
| `PAGE_COUNT` | Document Page Count | 5 | PDF & DOCX | Document length exceeding or falling short of exactly 1 page. | Single-page formatting ensures complete ATS ingestion and prevents multi-page truncation. | Trim spacing and bullet counts to fit content onto exactly 1 page. |
| `PARSER_AGREEMENT` | Dual-Parser Consistency | 10 | PDF | Divergence in extracted text between `pdfminer.six` and `pypdf` (measured via token overlap ratio). | High discrepancy between standard extraction engines signals delicate PDF stream structures or encoding issues. | Re-export the PDF using a clean print engine like LibreOffice or Microsoft Word. |
| `FIELD_RECOVERY` | Profile Entity Recovery | 10 | PDF & DOCX | Proportion of candidate profile entities (name, email, phone, companies, job titles, skills) recovered from text. | Verifies that key candidate facts present in `profile.yaml` are discoverable in the generated document text. | Ensure all profile entries are typed as searchable plain text in the document body. |

---

## 3. Scoring Formula and Hard Caps

### Weight Calculation
Each check produces a score between `0.0` and `1.0`:
- `1.0`: Check passed completely.
- `0.5`: Warning or partial match (e.g., minor date inconsistency or partial entity recovery).
- `0.0`: Check failed.

When `--profile` is not provided, `FIELD_RECOVERY` is excluded from the active set and the denominator adjusts accordingly.

Let $w_i$ be the weight of active check $i$, and $s_i$ be its score. The base raw score $S_{\text{raw}}$ is:

$$S_{\text{raw}} = \frac{\sum_{i=1}^{N} (w_i \cdot s_i)}{\sum_{i=1}^{N} w_i} \times 100$$

### Hard Caps
Regardless of other passing checks, fatal parsing flaws enforce upper limits on the final score:

1. **Text Extraction Failure (`TEXT_EXTRACT` == 0.0):**
   If no text can be extracted (e.g., scanned image or unmapped fonts), the maximum possible score is capped at **20**:
   $$\text{Score} = \min(S_{\text{raw}}, 20)$$

2. **Contact Extraction Failure (`CONTACT` == 0.0):**
   If essential contact info is missing or completely unparseable, the maximum possible score is capped at **50**:
   $$\text{Score} = \min(S_{\text{raw}}, 50)$$

If both caps trigger, the lower cap takes precedence ($\le 20$).

---

## 4. Exit Codes

`forge ats-sim` communicates results via Unix standard exit codes:
- **`0`**: Document score $\ge 80$ (Passed parser fragility criteria).
- **`1`**: Document score $< 80$ (Failed one or more critical checks; needs attention).
- **`2`**: Usage or file error (file not found, corrupted stream, password protected, unsupported file format).

---

## 5. Limitations

1. **Not a Real ATS:** This tool does not interface with or mimic proprietary parsing algorithms from Workday, Taleo, iCIMS, or Greenhouse.
2. **No Semantic Semantic Relevance Judgment:** Passing this checker means the document is structurally readable by parsers. It does not evaluate whether candidate skills match a specific job description.
3. **No Ranking Simulation:** ATS systems often rank candidates based on keyword frequency, semantic embeddings, and recruiter-configured filters. This tool only evaluates file parseability and structural hygiene.
4. **Platform Font Differences:** Font metrics and PDF rendering can vary slightly across operating systems depending on installed font packs.
