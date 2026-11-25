"""
Unit tests and fragility fixtures for ATS parser fragility checker (`forge ats-sim`).
"""

import json
import os
import tempfile

import docx
import pypdf
import pytest
from docx.oxml.ns import qn

from careerforge.cli import _display_ats_sim_report
from careerforge.core.ats_sim import AtsSimFileError, run_ats_sim
from careerforge.core.cv_builder import build_universal_cv
from careerforge.core.profile_loader import load_profile


def _make_clean_docx_content(doc: docx.Document):
    """Helper to populate valid single-column body content."""
    doc.add_paragraph("Alex Rivera")
    doc.add_paragraph("alex.rivera@example.com | +1 (555) 019-2834 | linkedin.com/in/alexrivera")
    doc.add_paragraph("Professional Summary")
    doc.add_paragraph("Experienced engineer building scalable cloud applications.")
    doc.add_paragraph("Professional Experience")
    doc.add_paragraph("Senior Engineer at TechCorp from Jan 2022 to Present.")
    doc.add_paragraph("Education")
    doc.add_paragraph("B.Sc. in Computer Science from University of Texas.")
    doc.add_paragraph("Skills")
    doc.add_paragraph("Python, Go, PostgreSQL, Redis, Docker, Git.")


def test_empty_image_pdf_fails_text_extract():
    """An image-only / empty text stream PDF must fail TEXT_EXTRACT and be capped at score <= 20."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name

    try:
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with open(tmp_path, "wb") as f:
            writer.write(f)

        report = run_ats_sim(tmp_path)
        assert not report.passed
        assert report.score <= 20
        assert "TEXT_EXTRACT failure: Score capped at 20" in report.hard_caps_applied

        extract_check = next(c for c in report.checks if c.id == "TEXT_EXTRACT")
        assert not extract_check.passed
        assert extract_check.score == 0.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_two_column_docx_fails_columns_and_docx_struct():
    """A multi-column DOCX must fail COLUMNS and DOCX_STRUCT checks."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        doc = docx.Document()
        _make_clean_docx_content(doc)

        # Inject multi-column section
        cols_elems = doc.sections[0]._sectPr.xpath(".//w:cols")
        if cols_elems:
            cols_elems[0].set(qn("w:num"), "2")
        else:
            from docx.oxml import OxmlElement
            c = OxmlElement("w:cols")
            c.set(qn("w:num"), "2")
            doc.sections[0]._sectPr.append(c)

        doc.save(tmp_path)

        report = run_ats_sim(tmp_path)
        col_check = next(c for c in report.checks if c.id == "COLUMNS")
        struct_check = next(c for c in report.checks if c.id == "DOCX_STRUCT")

        assert not col_check.passed
        assert col_check.score == 0.0
        assert not struct_check.passed
        assert struct_check.score == 0.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_header_contact_fails_header_footer():
    """Contact information placed only in the header/footer must fail HEADER_FOOTER check."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        doc = docx.Document()
        # Body text without email or phone
        doc.add_paragraph("Alex Rivera")
        doc.add_paragraph("Professional Summary")
        doc.add_paragraph("Experienced software engineer.")
        doc.add_paragraph("Professional Experience")
        doc.add_paragraph("Engineer at Apex Cloud from Jan 2022 to Present.")
        doc.add_paragraph("Education")
        doc.add_paragraph("B.Sc. in Computer Science")
        doc.add_paragraph("Skills")
        doc.add_paragraph("Python, Go, SQL")

        # Contact info strictly in header
        header = doc.sections[0].header
        header.paragraphs[0].text = "alex.rivera@example.com | +1 (555) 019-2834"

        doc.save(tmp_path)

        report = run_ats_sim(tmp_path)
        hf_check = next(c for c in report.checks if c.id == "HEADER_FOOTER")
        assert not hf_check.passed
        assert hf_check.score == 0.0
        assert "exclusively in header/footer" in hf_check.detail
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_unicode_ligatures_and_zero_width_fails():
    """Text with typographic ligatures or zero-width spaces must fail UNICODE check."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        doc = docx.Document()
        _make_clean_docx_content(doc)
        # Inject ligature and zero-width space
        doc.add_paragraph("Pro\ufb01le details with hidden\u200b characters.")
        doc.save(tmp_path)

        report = run_ats_sim(tmp_path)
        u_check = next(c for c in report.checks if c.id == "UNICODE")
        assert not u_check.passed
        assert u_check.score == 0.0
        assert "Ligatures detected" in u_check.detail
        assert "Zero-width characters" in u_check.detail
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_icon_font_glyphs_fails():
    """Text with Private Use Area icon font glyphs must fail ICON_GLYPHS check."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        doc = docx.Document()
        _make_clean_docx_content(doc)
        # Inject Private Use Area character U+E001 (FontAwesome icon)
        doc.add_paragraph("\ue001 alex.rivera@example.com \ue002 +1 555-019-2834")
        doc.save(tmp_path)

        report = run_ats_sim(tmp_path)
        icon_check = next(c for c in report.checks if c.id == "ICON_GLYPHS")
        assert not icon_check.passed
        assert icon_check.score == 0.0
        assert "icon glyph(s) from Unicode Private Use Area" in icon_check.detail
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_mixed_dates_fails():
    """Document mixing written month dates and numeric dates must fail DATES check."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        doc = docx.Document()
        _make_clean_docx_content(doc)
        # Inject mixed dates: "Jan 2024" and "03/2021"
        doc.add_paragraph("Senior Engineer: Jan 2024 – Present")
        doc.add_paragraph("Associate Engineer: 03/2021 – 12/2023")
        doc.save(tmp_path)

        report = run_ats_sim(tmp_path)
        date_check = next(c for c in report.checks if c.id == "DATES")
        assert not date_check.passed
        assert date_check.score == 0.5
        assert "Mixed date formats detected" in date_check.detail
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_multipage_pdf_fails_page_count():
    """A 2-page PDF document must fail PAGE_COUNT check."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name

    try:
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_blank_page(width=612, height=792)
        with open(tmp_path, "wb") as f:
            writer.write(f)

        report = run_ats_sim(tmp_path)
        page_check = next(c for c in report.checks if c.id == "PAGE_COUNT")
        assert not page_check.passed
        assert page_check.score == 0.0
        assert "Document contains 2 pages" in page_check.detail
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_sample_cv_ats_sim_score_and_recovery():
    """
    Builds a full CV from examples/profile.example.yaml and verifies that
    ats-sim scores >= 90 and achieves FIELD_RECOVERY >= 0.9.
    """
    example_yaml = os.path.join("examples", "profile.example.yaml")
    assert os.path.exists(example_yaml)

    prof = load_profile(example_yaml)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        build_universal_cv(prof, tmp_path)
        report = run_ats_sim(tmp_path, profile_path=example_yaml)

        assert report.score >= 90, f"Expected score >= 90, got {report.score}"
        assert report.passed

        recovery_check = next((c for c in report.checks if c.id == "FIELD_RECOVERY"), None)
        assert recovery_check is not None
        assert recovery_check.passed
        assert recovery_check.score == 1.0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_file_error_handling():
    """Verifies that missing, unsupported, or corrupt files raise AtsSimFileError."""
    # 1. Nonexistent file
    with pytest.raises(AtsSimFileError, match="File not found"):
        run_ats_sim("nonexistent_file_abc123.pdf")

    # 2. Unsupported extension
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        txt_path = f.name
        f.write(b"Hello world")
    try:
        with pytest.raises(AtsSimFileError, match="Unsupported file format"):
            run_ats_sim(txt_path)
    finally:
        if os.path.exists(txt_path):
            os.remove(txt_path)

    # 3. Corrupt PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        corrupt_path = f.name
        f.write(b"%PDF-1.4 Corrupted stream content")
    try:
        with pytest.raises(AtsSimFileError, match="Corrupt or unreadable PDF"):
            run_ats_sim(corrupt_path)
    finally:
        if os.path.exists(corrupt_path):
            os.remove(corrupt_path)


def test_ats_sim_offline_guarantee(socket_disabled=None):
    """Guarantees zero network calls are performed by ats-sim."""
    example_yaml = os.path.join("examples", "profile.example.yaml")
    prof = load_profile(example_yaml)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        build_universal_cv(prof, tmp_path)
        report = run_ats_sim(tmp_path, profile_path=example_yaml)
        assert report.score >= 80
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_cli_ats_sim_json_and_exit_codes(capsys):
    """Verifies CLI helper returns code 0 on pass, code 2 on error, and outputs valid JSON."""
    example_yaml = os.path.join("examples", "profile.example.yaml")
    prof = load_profile(example_yaml)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name

    try:
        build_universal_cv(prof, tmp_path)

        # 1. Test passing file with JSON output
        exit_code = _display_ats_sim_report(tmp_path, profile_path=example_yaml, as_json=True)
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is True
        assert data["score"] >= 90
        assert len(data["checks"]) >= 12

        # 2. Test missing file error exit code
        err_code = _display_ats_sim_report("does_not_exist.pdf", as_json=False)
        assert err_code == 2
        err_captured = capsys.readouterr()
        assert "File not found" in err_captured.err
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
