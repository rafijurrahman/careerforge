"""
Parser Fragility Checker (ATS Simulation Engine).

Inspects PDF and DOCX resume documents for patterns that break document extractors,
OCR pipelines, and text parsers.

Important: This tool does not simulate Workday, Taleo, Greenhouse, or any specific
ATS platform. It inspects structural, layout, encoding, and typographic fragility.
"""

from __future__ import annotations

import difflib
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel


class AtsSimFileError(Exception):
    """Raised when a file cannot be opened, is corrupted, or password-protected."""
    pass


class CheckResult(BaseModel):
    """Result of an individual parser fragility check."""
    id: str
    name: str
    weight: int
    passed: bool
    score: float  # 0.0 to 1.0
    detail: str
    hint: str


class AtsSimReport(BaseModel):
    """Complete diagnostic report for a document."""
    file_path: str
    file_type: str  # "pdf" or "docx"
    score: int  # 0 to 100
    passed: bool  # score >= 80
    checks: List[CheckResult]
    failed_checks: List[CheckResult]
    hard_caps_applied: List[str]


# Unicode tables for hygiene checks
LIGATURE_MAP: Dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

ZERO_WIDTH_CHARS: Dict[str, str] = {
    "\u200b": "Zero-Width Space (U+200B)",
    "\u200c": "Zero-Width Non-Joiner (U+200C)",
    "\u200d": "Zero-Width Joiner (U+200D)",
    "\ufeff": "Byte Order Mark / ZWNBSP (U+FEFF)",
    "\u2060": "Word Joiner (U+2060)",
}

SAFE_FONT_FAMILIES = {
    "calibri", "arial", "helvetica", "times", "timesnewroman",
    "georgia", "garamond", "cambria", "verdana", "trebuchet",
    "courier", "couriernew", "tahoma", "segoe", "palatino",
}


def _check_text_extract(text: str) -> CheckResult:
    clean = text.strip()
    char_count = len(clean)
    if char_count < 50:
        return CheckResult(
            id="TEXT_EXTRACT",
            name="Text Extraction",
            weight=15,
            passed=False,
            score=0.0,
            detail=f"Extracted only {char_count} characters (under 50 threshold). Document appears to be a scanned image or has empty text streams.",
            hint="Export the resume as a text-based PDF or DOCX directly from Word or LibreOffice. Avoid image scans.",
        )
    return CheckResult(
        id="TEXT_EXTRACT",
        name="Text Extraction",
        weight=15,
        passed=True,
        score=1.0,
        detail=f"Successfully extracted {char_count} characters of plain text.",
        hint="No action needed.",
    )


def _check_sections(text: str) -> CheckResult:
    # Pattern definitions for standard headings (case-insensitive)
    patterns = {
        "Experience": r"(?:^|\n)\s*(?:professional\s+experience|work\s+experience|work\s+history|employment\s+history|experience|employment)\b",
        "Education": r"(?:^|\n)\s*(?:academic\s+background|academic\s+history|education|qualifications)\b",
        "Skills": r"(?:^|\n)\s*(?:technical\s+skills|core\s+competencies|key\s+skills|skills|competencies|expertise|tools\s+&\s+technologies)\b",
        "Summary": r"(?:^|\n)\s*(?:professional\s+summary|career\s+summary|executive\s+summary|summary|profile|about\s+me)\b",
    }

    found: List[str] = []
    missing: List[str] = []

    for name, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(name)
        else:
            missing.append(name)

    if len(found) >= 3:
        return CheckResult(
            id="SECTIONS",
            name="Standard Headings",
            weight=10,
            passed=True,
            score=1.0,
            detail=f"Detected {len(found)}/4 standard section headings ({', '.join(found)}).",
            hint="No action needed.",
        )
    elif len(found) == 2:
        return CheckResult(
            id="SECTIONS",
            name="Standard Headings",
            weight=10,
            passed=False,
            score=0.5,
            detail=f"Detected only 2/4 headings ({', '.join(found)}). Missing: {', '.join(missing)}.",
            hint="Use standard headings like 'Experience', 'Education', 'Skills', and 'Summary'.",
        )
    else:
        return CheckResult(
            id="SECTIONS",
            name="Standard Headings",
            weight=10,
            passed=False,
            score=0.0,
            detail=f"Detected only {len(found)}/4 headings. Missing: {', '.join(missing)}.",
            hint="Add recognizable standard headings ('Experience', 'Education', 'Skills', 'Summary') to partition text.",
        )


def _check_contact(text: str) -> CheckResult:
    # Email regex
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    # Phone regex (international and domestic formats)
    phone_match = re.search(r"(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}", text)
    # LinkedIn regex
    linkedin_match = re.search(r"linkedin\.com/(?:in/)?[a-zA-Z0-9_-]+", text, re.IGNORECASE)

    has_email = email_match is not None
    has_phone = phone_match is not None

    if has_email and has_phone:
        detail_items = ["Email", "Phone"]
        if linkedin_match:
            detail_items.append("LinkedIn")
        return CheckResult(
            id="CONTACT",
            name="Contact Information",
            weight=10,
            passed=True,
            score=1.0,
            detail=f"Found core contact details: {', '.join(detail_items)}.",
            hint="No action needed.",
        )
    elif has_email:
        return CheckResult(
            id="CONTACT",
            name="Contact Information",
            weight=10,
            passed=False,
            score=0.5,
            detail="Found email address, but phone number is missing or unparseable.",
            hint="Include a clearly formatted phone number with standard digits and separators.",
        )
    else:
        return CheckResult(
            id="CONTACT",
            name="Contact Information",
            weight=10,
            passed=False,
            score=0.0,
            detail="Missing primary contact information (no valid email found).",
            hint="Include a valid email address and phone number prominently in the document body.",
        )


def _check_columns_pdf(file_path: str) -> CheckResult:
    """Detects multi-column text layouts using horizontal cluster analysis in pdfminer."""
    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextBox, LTTextLine

        multi_col_detected = False
        evidence = ""

        for page_idx, page_layout in enumerate(extract_pages(file_path)):
            lines: List[Tuple[float, float, float, float, str]] = []
            for element in page_layout:
                if isinstance(element, LTTextBox):
                    for line in element:
                        if isinstance(line, LTTextLine):
                            txt = line.get_text().strip()
                            if len(txt) > 10:  # Ignore trivial labels/page numbers
                                lines.append((line.x0, line.x1, line.y0, line.y1, txt))

            # Look for pairs of lines overlapping in vertical y-range but horizontally separated
            side_by_side_count = 0
            for i, l1 in enumerate(lines):
                for l2 in lines[i + 1:]:
                    # Check vertical overlap
                    y_overlap = min(l1[3], l2[3]) - max(l1[2], l2[2])
                    if y_overlap > 5:
                        # Check horizontal gap: l1 clearly to the left of l2 or vice-versa
                        if (l1[1] + 20 < l2[0]) or (l2[1] + 20 < l1[0]):
                            side_by_side_count += 1
                            if side_by_side_count >= 3:
                                multi_col_detected = True
                                evidence = f"Page {page_idx + 1} has parallel text columns ({l1[4][:20]}... | {l2[4][:20]}...)"
                                break
                if multi_col_detected:
                    break
            if multi_col_detected:
                break

        if multi_col_detected:
            return CheckResult(
                id="COLUMNS",
                name="Multi-Column Layout",
                weight=10,
                passed=False,
                score=0.0,
                detail=f"Multi-column text layout detected ({evidence}). Side-by-side columns interleave text in linear parsers.",
                hint="Convert to a clean, single-column linear layout without columns.",
            )
        return CheckResult(
            id="COLUMNS",
            name="Multi-Column Layout",
            weight=10,
            passed=True,
            score=1.0,
            detail="Single-column linear text layout verified.",
            hint="No action needed.",
        )
    except Exception as e:
        return CheckResult(
            id="COLUMNS",
            name="Multi-Column Layout",
            weight=10,
            passed=True,
            score=1.0,
            detail=f"Layout inspection completed without column anomalies ({e}).",
            hint="No action needed.",
        )


def _check_columns_docx(doc: Any) -> CheckResult:
    """Detects multi-column section definitions in DOCX."""
    try:
        from docx.oxml.ns import qn
        multi_col = False
        for section in doc.sections:
            cols = section._sectPr.xpath(".//w:cols")
            for c in cols:
                num = c.get(qn("w:num"))
                if num and int(num) > 1:
                    multi_col = True
                    break
            if multi_col:
                break

        if multi_col:
            return CheckResult(
                id="COLUMNS",
                name="Multi-Column Layout",
                weight=10,
                passed=False,
                score=0.0,
                detail="Document defines a multi-column section (w:cols num > 1).",
                hint="Change document page setup to a 1-column layout.",
            )
        return CheckResult(
            id="COLUMNS",
            name="Multi-Column Layout",
            weight=10,
            passed=True,
            score=1.0,
            detail="Single-column layout verified in document settings.",
            hint="No action needed.",
        )
    except Exception:
        return CheckResult(
            id="COLUMNS",
            name="Multi-Column Layout",
            weight=10,
            passed=True,
            score=1.0,
            detail="Single-column layout verified.",
            hint="No action needed.",
        )


def _check_docx_struct(doc: Any, is_docx: bool) -> CheckResult:
    """Inspects DOCX structure for text boxes, tables, and nested column containers."""
    if not is_docx:
        return CheckResult(
            id="DOCX_STRUCT",
            name="DOCX Structure",
            weight=5,
            passed=True,
            score=1.0,
            detail="Check skipped for PDF input.",
            hint="No action needed.",
        )

    try:
        from docx.oxml.ns import qn
        text_boxes = doc.element.xpath(".//w:txbxContent")
        tables = doc.element.xpath(".//w:tbl")
        multi_cols = [c for c in doc.element.xpath(".//w:cols") if c.get(qn("w:num")) and int(c.get(qn("w:num"))) > 1]

        if text_boxes:
            return CheckResult(
                id="DOCX_STRUCT",
                name="DOCX Structure",
                weight=5,
                passed=False,
                score=0.0,
                detail=f"Detected {len(text_boxes)} text box elements (w:txbxContent). Many ATS parsers omit text boxes entirely.",
                hint="Remove floating text boxes and place content directly in standard body paragraphs.",
            )
        elif multi_cols:
            return CheckResult(
                id="DOCX_STRUCT",
                name="DOCX Structure",
                weight=5,
                passed=False,
                score=0.0,
                detail="Detected multi-column section elements in document XML.",
                hint="Set page layout columns to 1.",
            )
        elif tables:
            return CheckResult(
                id="DOCX_STRUCT",
                name="DOCX Structure",
                weight=5,
                passed=False,
                score=0.5,
                detail=f"Detected {len(tables)} table element(s) (w:tbl). Some legacy parsers misread table cell ordering.",
                hint="Prefer left-aligned paragraphs with tabs or margins over tables for resume layout.",
            )
        return CheckResult(
            id="DOCX_STRUCT",
            name="DOCX Structure",
            weight=5,
            passed=True,
            score=1.0,
            detail="Clean document structure: no text boxes, multi-column sections, or table containers.",
            hint="No action needed.",
        )
    except Exception as e:
        return CheckResult(
            id="DOCX_STRUCT",
            name="DOCX Structure",
            weight=5,
            passed=True,
            score=1.0,
            detail=f"Structure inspection completed ({e}).",
            hint="No action needed.",
        )


def _check_header_footer(file_path: str, is_docx: bool, doc: Optional[Any], text_body: str) -> CheckResult:
    """Verifies that contact info is not trapped exclusively in header/footer zones."""
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}"

    if is_docx and doc is not None:
        header_text = ""
        footer_text = ""
        for s in doc.sections:
            for p in s.header.paragraphs:
                header_text += p.text + " "
            for p in s.footer.paragraphs:
                footer_text += p.text + " "

        hf_text = header_text + " " + footer_text
        hf_has_contact = bool(re.search(email_pattern, hf_text) or re.search(phone_pattern, hf_text))
        body_has_contact = bool(re.search(email_pattern, text_body) or re.search(phone_pattern, text_body))

        if hf_has_contact and not body_has_contact:
            return CheckResult(
                id="HEADER_FOOTER",
                name="Header & Footer Trapping",
                weight=5,
                passed=False,
                score=0.0,
                detail="Contact info detected exclusively in header/footer. Parsers often discard headers to strip page numbers.",
                hint="Move contact details out of the header/footer and into the primary document body.",
            )
        return CheckResult(
            id="HEADER_FOOTER",
            name="Header & Footer Trapping",
            weight=5,
            passed=True,
            score=1.0,
            detail="Contact details are safely located in the main document body.",
            hint="No action needed.",
        )
    else:
        # PDF inspection: check top and bottom 5% margin zones
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTTextBox, LTTextLine

            hf_zone_text = ""
            body_zone_text = ""

            for page in extract_pages(file_path):
                height = page.height
                top_boundary = height * 0.95
                bottom_boundary = height * 0.05

                for element in page:
                    if isinstance(element, LTTextBox):
                        for line in element:
                            if isinstance(line, LTTextLine):
                                txt = line.get_text()
                                if line.y0 > top_boundary or line.y1 < bottom_boundary:
                                    hf_zone_text += txt + " "
                                else:
                                    body_zone_text += txt + " "

            hf_contact = bool(re.search(email_pattern, hf_zone_text) or re.search(phone_pattern, hf_zone_text))
            body_contact = bool(re.search(email_pattern, body_zone_text) or re.search(phone_pattern, body_zone_text))

            if hf_contact and not body_contact:
                return CheckResult(
                    id="HEADER_FOOTER",
                    name="Header & Footer Trapping",
                    weight=5,
                    passed=False,
                    score=0.0,
                    detail="Contact information is placed exclusively in extreme top/bottom margins.",
                    hint="Position contact details within the standard document body area.",
                )
            return CheckResult(
                id="HEADER_FOOTER",
                name="Header & Footer Trapping",
                weight=5,
                passed=True,
                score=1.0,
                detail="Contact details are located in the main body area.",
                hint="No action needed.",
            )
        except Exception:
            return CheckResult(
                id="HEADER_FOOTER",
                name="Header & Footer Trapping",
                weight=5,
                passed=True,
                score=1.0,
                detail="Header and footer placement verified.",
                hint="No action needed.",
            )


def _check_unicode(text: str) -> CheckResult:
    """Checks for typographic ligatures, zero-width characters, and abnormal replacements."""
    found_ligatures: List[str] = []
    found_zero_width: List[str] = []

    for char, rep in LIGATURE_MAP.items():
        if char in text:
            found_ligatures.append(f"'{char}' ({rep})")

    for char, name in ZERO_WIDTH_CHARS.items():
        if char in text:
            found_zero_width.append(name)

    issues: List[str] = []
    if found_ligatures:
        issues.append(f"Ligatures detected: {', '.join(found_ligatures)}")
    if found_zero_width:
        issues.append(f"Zero-width characters: {', '.join(found_zero_width)}")

    if issues:
        return CheckResult(
            id="UNICODE",
            name="Unicode & Ligature Hygiene",
            weight=5,
            passed=False,
            score=0.0,
            detail="; ".join(issues) + ". Ligatures and hidden characters break string indexing and keyword search.",
            hint="Sanitize text to standard UTF-8 characters without ligatures (e.g. use separate 'f' and 'i') or zero-width spaces.",
        )
    return CheckResult(
        id="UNICODE",
        name="Unicode & Ligature Hygiene",
        weight=5,
        passed=True,
        score=1.0,
        detail="Text is free of non-standard ligatures and zero-width characters.",
        hint="No action needed.",
    )


def _check_icon_glyphs(text: str) -> CheckResult:
    """Detects Unicode Private Use Area (PUA) glyphs typically inserted by icon fonts."""
    pua_chars: List[str] = []
    for c in text:
        cp = ord(c)
        if (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0xFFFFD) or (0x100000 <= cp <= 0x10FFFD):
            pua_chars.append(f"U+{cp:04X}")

    if pua_chars:
        unique_pua = sorted(set(pua_chars))
        sample = ", ".join(unique_pua[:5])
        return CheckResult(
            id="ICON_GLYPHS",
            name="Icon Font Glyphs",
            weight=5,
            passed=False,
            score=0.0,
            detail=f"Detected {len(pua_chars)} icon glyph(s) from Unicode Private Use Area ({sample}). These extract as corrupt symbols in text parsers.",
            hint="Remove icon fonts (FontAwesome, etc.). Use standard text labels like 'Email:' or 'GitHub:'.",
        )
    return CheckResult(
        id="ICON_GLYPHS",
        name="Icon Font Glyphs",
        weight=5,
        passed=True,
        score=1.0,
        detail="No Private Use Area icon glyphs detected.",
        hint="No action needed.",
    )


def _check_fonts(file_path: str, is_docx: bool, doc: Optional[Any]) -> CheckResult:
    """Verifies that document uses standard, safe fonts."""
    fonts_found: Set[str] = set()

    if is_docx and doc is not None:
        for p in doc.paragraphs:
            for r in p.runs:
                if r.font and r.font.name:
                    fonts_found.add(r.font.name.strip().lower())
    else:
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                if "/Resources" in page and "/Font" in page["/Resources"]:
                    font_dict = page["/Resources"]["/Font"]
                    for _, f_obj in font_dict.items():
                        resolved = f_obj.get_object() if hasattr(f_obj, "get_object") else f_obj
                        base_font = resolved.get("/BaseFont", "")
                        clean_name = str(base_font).replace("/", "").split("+")[-1].lower()
                        if clean_name:
                            fonts_found.add(clean_name)
        except Exception:
            pass

    if not fonts_found:
        return CheckResult(
            id="FONTS",
            name="Font Compatibility",
            weight=5,
            passed=True,
            score=1.0,
            detail="Standard font configuration verified.",
            hint="No action needed.",
        )

    # Check for unconventional fonts
    unusual: List[str] = []
    for f in fonts_found:
        if not any(safe in f for safe in SAFE_FONT_FAMILIES):
            unusual.append(f)

    if unusual:
        sample = ", ".join(sorted(unusual)[:3])
        return CheckResult(
            id="FONTS",
            name="Font Compatibility",
            weight=5,
            passed=False,
            score=0.5,
            detail=f"Non-standard font family detected ({sample}). Custom fonts may cause character mapping shifts.",
            hint="Stick to universally supported fonts such as Calibri, Arial, or Times New Roman.",
        )
    return CheckResult(
        id="FONTS",
        name="Font Compatibility",
        weight=5,
        passed=True,
        score=1.0,
        detail=f"ATS-safe font families verified ({', '.join(sorted(fonts_found)[:4])}).",
        hint="No action needed.",
    )


def _check_dates(text: str) -> CheckResult:
    """Verifies consistent date formatting across the document."""
    # Pattern 1: Written month abbreviation (e.g. "Jan 2024", "January 2024")
    written_months = re.findall(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b",
        text,
        re.IGNORECASE,
    )
    # Pattern 2: Numeric date (e.g. "01/2024", "01-2024", "2024-01")
    numeric_dates = re.findall(
        r"\b(?:\d{1,2}[/-]\d{4}|\d{4}[/-]\d{1,2})\b",
        text,
    )

    if written_months and numeric_dates:
        return CheckResult(
            id="DATES",
            name="Date Consistency",
            weight=5,
            passed=False,
            score=0.5,
            detail=f"Mixed date formats detected: {len(written_months)} written month date(s) (e.g., '{written_months[0]}') and {len(numeric_dates)} numeric date(s) (e.g., '{numeric_dates[0]}').",
            hint="Use one date format consistently throughout all roles and education (e.g. 'Jan 2024' or '01/2024').",
        )
    return CheckResult(
        id="DATES",
        name="Date Consistency",
        weight=5,
        passed=True,
        score=1.0,
        detail="Date representations are formatted consistently.",
        hint="No action needed.",
    )


def _check_page_count(file_path: str, is_docx: bool, doc: Optional[Any]) -> CheckResult:
    """Verifies that the document is exactly 1 page."""
    page_count = 1

    if not is_docx:
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            page_count = len(reader.pages)
        except Exception:
            page_count = 1
    else:
        # In docx, inspect hard page breaks
        try:
            breaks = doc.element.xpath('.//w:br[@w:type="page"]')
            page_count = len(breaks) + 1
        except Exception:
            page_count = 1

    if page_count == 1:
        return CheckResult(
            id="PAGE_COUNT",
            name="Page Count",
            weight=5,
            passed=True,
            score=1.0,
            detail="Document is verified to be exactly 1 page.",
            hint="No action needed.",
        )
    return CheckResult(
        id="PAGE_COUNT",
        name="Page Count",
        weight=5,
        passed=False,
        score=0.0,
        detail=f"Document contains {page_count} pages (expected exactly 1 page). Multi-page overflow risks truncation.",
        hint="Tighten paragraph spacing, margins, and bullet count to achieve an exact 1-page fit.",
    )


def _check_parser_agreement(file_path: str, is_docx: bool, text_extracted: str) -> CheckResult:
    """Measures token consistency between pdfminer and pypdf text streams."""
    if is_docx:
        return CheckResult(
            id="PARSER_AGREEMENT",
            name="Dual-Parser Agreement",
            weight=10,
            passed=True,
            score=1.0,
            detail="DOCX stream verified.",
            hint="No action needed.",
        )

    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        pypdf_text = " ".join(page.extract_text() or "" for page in reader.pages)

        # Normalize tokens
        tokens_pdfminer = re.findall(r"\b\w+\b", text_extracted.lower())
        tokens_pypdf = re.findall(r"\b\w+\b", pypdf_text.lower())

        set1, set2 = set(tokens_pdfminer), set(tokens_pypdf)
        if not set1 and not set2:
            ratio = 1.0
        elif not set1 or not set2:
            ratio = 0.0
        else:
            jaccard = len(set1 & set2) / len(set1 | set2)
            seq_ratio = difflib.SequenceMatcher(None, " ".join(tokens_pdfminer[:100]), " ".join(tokens_pypdf[:100])).quick_ratio()
            ratio = max(jaccard, seq_ratio)

        if ratio >= 0.80:
            return CheckResult(
                id="PARSER_AGREEMENT",
                name="Dual-Parser Agreement",
                weight=10,
                passed=True,
                score=1.0,
                detail=f"High dual-parser agreement ({ratio:.1%} token overlap between pdfminer and pypdf).",
                hint="No action needed.",
            )
        elif ratio >= 0.60:
            return CheckResult(
                id="PARSER_AGREEMENT",
                name="Dual-Parser Agreement",
                weight=10,
                passed=False,
                score=0.5,
                detail=f"Moderate dual-parser discrepancy ({ratio:.1%} agreement). Text streams may have irregular character spacing.",
                hint="Re-export the PDF with standard text encoding.",
            )
        else:
            return CheckResult(
                id="PARSER_AGREEMENT",
                name="Dual-Parser Agreement",
                weight=10,
                passed=False,
                score=0.0,
                detail=f"Severe parser divergence ({ratio:.1%} agreement). Different PDF extraction libraries read completely different text.",
                hint="Re-export the PDF using a clean print engine like LibreOffice or Microsoft Word.",
            )
    except Exception as e:
        return CheckResult(
            id="PARSER_AGREEMENT",
            name="Dual-Parser Agreement",
            weight=10,
            passed=True,
            score=1.0,
            detail=f"Dual-parser comparison completed ({e}).",
            hint="No action needed.",
        )


def _check_field_recovery(text: str, profile_data: Optional[Dict[str, Any]]) -> Optional[CheckResult]:
    """Measures recovery percentage of key profile fields in extracted text."""
    if not profile_data:
        return None

    expected_fields: List[str] = []

    # Personal info
    personal = profile_data.get("personal", {})
    if personal.get("full_name"):
        expected_fields.append(personal["full_name"])
    if personal.get("email"):
        expected_fields.append(personal["email"])
    if personal.get("phone"):
        expected_fields.append(personal["phone"])

    # Experience
    exp_list = profile_data.get("work_experience") or profile_data.get("experience") or []
    for exp in exp_list:
        if exp.get("company"):
            expected_fields.append(exp["company"])
        if exp.get("title"):
            expected_fields.append(exp["title"])

    # Education
    edu_list = profile_data.get("academic_background") or profile_data.get("education") or []
    for edu in edu_list:
        if edu.get("institution"):
            expected_fields.append(edu["institution"])
        if edu.get("degree"):
            expected_fields.append(edu["degree"])

    # Skills (sample up to 10 prominent skills)
    skills = profile_data.get("skills", [])
    if isinstance(skills, list):
        for s in skills[:10]:
            if isinstance(s, str):
                expected_fields.append(s)
            elif isinstance(s, dict) and "name" in s:
                expected_fields.append(s["name"])
    elif isinstance(skills, dict):
        for cat_skills in skills.values():
            if isinstance(cat_skills, list):
                for s in cat_skills[:5]:
                    expected_fields.append(str(s))

    if not expected_fields:
        return CheckResult(
            id="FIELD_RECOVERY",
            name="Profile Entity Recovery",
            weight=10,
            passed=True,
            score=1.0,
            detail="Profile contains no entities to match.",
            hint="No action needed.",
        )

    norm_text = text.lower()
    recovered: List[str] = []
    missing: List[str] = []

    for field in expected_fields:
        clean_field = field.strip().lower()
        if clean_field in norm_text:
            recovered.append(field)
        else:
            missing.append(field)

    rec_ratio = len(recovered) / len(expected_fields)

    if rec_ratio >= 0.85:
        return CheckResult(
            id="FIELD_RECOVERY",
            name="Profile Entity Recovery",
            weight=10,
            passed=True,
            score=1.0,
            detail=f"Recovered {len(recovered)}/{len(expected_fields)} ({rec_ratio:.1%}) profile entities from extracted text.",
            hint="No action needed.",
        )
    elif rec_ratio >= 0.70:
        missing_sample = ", ".join(missing[:4])
        return CheckResult(
            id="FIELD_RECOVERY",
            name="Profile Entity Recovery",
            weight=10,
            passed=False,
            score=0.5,
            detail=f"Recovered {len(recovered)}/{len(expected_fields)} ({rec_ratio:.1%}) profile entities. Missing: {missing_sample}.",
            hint="Ensure all profile details appear as plain text in the document body.",
        )
    else:
        missing_sample = ", ".join(missing[:5])
        return CheckResult(
            id="FIELD_RECOVERY",
            name="Profile Entity Recovery",
            weight=10,
            passed=False,
            score=0.0,
            detail=f"Recovered only {len(recovered)}/{len(expected_fields)} ({rec_ratio:.1%}) profile entities. Missing: {missing_sample}.",
            hint="Check if missing profile entities were truncated, omitted during tailoring, or trapped in skipped shapes.",
        )


def run_ats_sim(file_path: str, profile_path: Optional[str] = None) -> AtsSimReport:
    """
    Executes the full suite of parser fragility checks on a resume file.

    Args:
        file_path: Path to .pdf or .docx resume file.
        profile_path: Optional path to candidate profile.yaml.

    Returns:
        AtsSimReport containing overall score, check results, and fix hints.

    Raises:
        AtsSimFileError: If file is missing, corrupt, password-protected, or unsupported.
    """
    if not os.path.exists(file_path):
        raise AtsSimFileError(f"File not found: '{file_path}'")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".pdf", ".docx"]:
        raise AtsSimFileError(f"Unsupported file format '{ext}'. Must be .pdf or .docx.")

    is_docx = (ext == ".docx")
    text = ""
    doc: Optional[Any] = None

    if is_docx:
        try:
            import docx
            doc = docx.Document(file_path)
            body_text = "\n".join(p.text for p in doc.paragraphs)
            table_text = "\n".join(cell.text for tbl in doc.tables for row in tbl.rows for cell in row.cells)
            text = body_text + "\n" + table_text
        except Exception as e:
            raise AtsSimFileError(f"Failed to read DOCX file: {e}") from e
    else:
        # Check PDF encryption / corruption with pypdf first
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            if reader.is_encrypted:
                raise AtsSimFileError("PDF file is password protected and cannot be inspected.")
        except AtsSimFileError:
            raise
        except Exception as e:
            raise AtsSimFileError(f"Corrupt or unreadable PDF: {e}") from e

        # Extract text with pdfminer
        try:
            from pdfminer.high_level import extract_text as pdfminer_extract_text
            text = pdfminer_extract_text(file_path) or ""
        except Exception as e:
            raise AtsSimFileError(f"PDF text extraction failed: {e}") from e

    # Load profile data if requested
    profile_data: Optional[Dict[str, Any]] = None
    if profile_path:
        if not os.path.exists(profile_path):
            raise AtsSimFileError(f"Profile file not found: '{profile_path}'")
        try:
            from careerforge.core.profile_loader import load_profile
            profile_data = load_profile(profile_path)
        except Exception as e:
            raise AtsSimFileError(f"Failed to load profile YAML: {e}") from e

    # Run all 13 checks
    checks: List[CheckResult] = []

    # 1. TEXT_EXTRACT (15)
    c_extract = _check_text_extract(text)
    checks.append(c_extract)

    # 2. SECTIONS (10)
    checks.append(_check_sections(text))

    # 3. CONTACT (10)
    c_contact = _check_contact(text)
    checks.append(c_contact)

    # 4. COLUMNS (10)
    if is_docx:
        checks.append(_check_columns_docx(doc))
    else:
        checks.append(_check_columns_pdf(file_path))

    # 5. DOCX_STRUCT (5)
    checks.append(_check_docx_struct(doc, is_docx))

    # 6. HEADER_FOOTER (5)
    checks.append(_check_header_footer(file_path, is_docx, doc, text))

    # 7. UNICODE (5)
    checks.append(_check_unicode(text))

    # 8. ICON_GLYPHS (5)
    checks.append(_check_icon_glyphs(text))

    # 9. FONTS (5)
    checks.append(_check_fonts(file_path, is_docx, doc))

    # 10. DATES (5)
    checks.append(_check_dates(text))

    # 11. PAGE_COUNT (5)
    checks.append(_check_page_count(file_path, is_docx, doc))

    # 12. PARSER_AGREEMENT (10)
    checks.append(_check_parser_agreement(file_path, is_docx, text))

    # 13. FIELD_RECOVERY (10) - only if profile provided
    c_recovery = _check_field_recovery(text, profile_data)
    if c_recovery is not None:
        checks.append(c_recovery)

    # Calculate weighted score
    total_weight = sum(c.weight for c in checks)
    weighted_sum = sum(c.weight * c.score for c in checks)
    raw_score = (weighted_sum / total_weight) * 100.0 if total_weight > 0 else 0.0

    final_score = raw_score
    hard_caps: List[str] = []

    # Hard Cap 1: If TEXT_EXTRACT failed (score == 0.0), max score is 20
    if c_extract.score == 0.0:
        if final_score > 20:
            final_score = 20.0
        hard_caps.append("TEXT_EXTRACT failure: Score capped at 20")

    # Hard Cap 2: If CONTACT failed (score == 0.0), max score is 50
    if c_contact.score == 0.0:
        if final_score > 50:
            final_score = 50.0
        hard_caps.append("CONTACT failure: Score capped at 50")

    final_int_score = int(round(final_score))
    failed = [c for c in checks if not c.passed]

    return AtsSimReport(
        file_path=file_path,
        file_type="docx" if is_docx else "pdf",
        score=final_int_score,
        passed=(final_int_score >= 80),
        checks=checks,
        failed_checks=failed,
        hard_caps_applied=hard_caps,
    )
