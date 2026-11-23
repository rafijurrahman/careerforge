"""
Universal ATS CV Builder.
Builds single-page, ATS-compliant docx documents for ANY professional role using python-docx.
"""

import os

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

try:
    from careerforge.core.link_embedder import add_hyperlink
except ImportError:
    from core.link_embedder import add_hyperlink

def set_cell_margins(cell, top=6, bottom=6, left=10, right=10):
    """Sets internal cell padding in docx tables."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def add_header_border(paragraph, color_hex="0F172A"):
    """Adds a crisp bottom border under section headers."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                     f'<w:bottom w:val="single" w:sz="6" w:space="2" w:color="{color_hex}"/>'
                     f'</w:pBdr>')
    pPr.append(pBdr)

def build_universal_cv(profile_data: dict, output_path: str, font_scale=1.0, spacing_scale=1.0, top_m=0.28, bot_m=0.26):
    """
    Builds a professional, ATS-optimized Word CV tailored from the profile dictionary.
    """
    doc = docx.Document()

    # Page Setup - Strictly 1 Page layout, fully utilizes page space
    sec = doc.sections[0]
    sec.top_margin = Inches(top_m)
    sec.bottom_margin = Inches(bot_m)
    sec.left_margin = Inches(0.48)
    sec.right_margin = Inches(0.48)
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11.0)

    # Palette
    PRIMARY = RGBColor(0x0F, 0x17, 0x2A)    # Deep Slate
    SECONDARY = RGBColor(0x02, 0x84, 0xC7)  # Slate Blue
    TEXT_DARK = RGBColor(0x1E, 0x29, 0x3B)  # Charcoal Body
    MUTED = RGBColor(0x47, 0x55, 0x69)      # Slate Gray
    LINK_COLOR = (2, 132, 199)

    personal = profile_data.get("personal", {})

    # ------------------ HEADER: NAME & TITLE ------------------
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(1.5 * spacing_scale)
    r_name = p_name.add_run(personal.get("full_name", "").upper())
    r_name.font.name = "Calibri"
    r_name.font.size = Pt(16.5 * font_scale)
    r_name.font.bold = True
    r_name.font.color.rgb = PRIMARY

    header_title = personal.get("header_title", "")
    if header_title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(2.0 * spacing_scale)
        r_title = p_title.add_run(header_title)
        r_title.font.name = "Calibri"
        r_title.font.size = Pt(10.0 * font_scale)
        r_title.font.bold = True
        r_title.font.color.rgb = SECONDARY

    # ------------------ CONTACT INFO WITH HYPERLINKS ------------------
    p_contact1 = doc.add_paragraph()
    p_contact1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact1.paragraph_format.space_before = Pt(0)
    p_contact1.paragraph_format.space_after = Pt(1.2 * spacing_scale)

    email = personal.get("email", "")
    phone = personal.get("phone", "")
    loc = personal.get("location", "")

    if email:
        add_hyperlink(p_contact1, f"mailto:{email}", email, font_size=8.8 * font_scale, color_rgb=(71, 85, 105))
    if phone:
        if email:
            r_sep = p_contact1.add_run("   |   ")
            r_sep.font.name = "Calibri"
            r_sep.font.size = Pt(8.8 * font_scale)
            r_sep.font.color.rgb = MUTED
        add_hyperlink(p_contact1, f"tel:{phone.replace(' ', '')}", phone, font_size=8.8 * font_scale, color_rgb=(71, 85, 105))
    if loc:
        r_loc = p_contact1.add_run(f"   |   {loc}")
        r_loc.font.name = "Calibri"
        r_loc.font.size = Pt(8.8 * font_scale)
        r_loc.font.color.rgb = MUTED

    p_contact2 = doc.add_paragraph()
    p_contact2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_contact2.paragraph_format.space_before = Pt(0)
    p_contact2.paragraph_format.space_after = Pt(2.8 * spacing_scale)

    links_to_add = []
    if personal.get("linkedin"):
        links_to_add.append(("linkedin", personal.get("linkedin"), personal.get("linkedin").replace("https://", "")))
    if personal.get("github"):
        links_to_add.append(("github", personal.get("github"), personal.get("github").replace("https://", "")))
    if personal.get("portfolio"):
        links_to_add.append(("portfolio", personal.get("portfolio"), f"Portfolio: {personal.get('portfolio').replace('https://', '')}"))

    for idx, (label, url, display_text) in enumerate(links_to_add):
        if idx > 0:
            r_sep = p_contact2.add_run("   |   ")
            r_sep.font.name = "Calibri"
            r_sep.font.size = Pt(8.8 * font_scale)
            r_sep.font.color.rgb = MUTED
        add_hyperlink(p_contact2, url, display_text, font_size=8.8 * font_scale, color_rgb=LINK_COLOR, bold=True)

    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3.8 * spacing_scale)
        p.paragraph_format.space_after = Pt(1.8 * spacing_scale)
        p.paragraph_format.keep_with_next = True
        add_header_border(p)
        r = p.add_run(title.upper())
        r.font.name = "Calibri"
        r.font.size = Pt(9.6 * font_scale)
        r.font.bold = True
        r.font.color.rgb = PRIMARY
        return p

    # ------------------ PROFESSIONAL SUMMARY ------------------
    summary_text = profile_data.get("professional_summary", "").strip()
    if summary_text:
        add_section_header("Professional Summary")
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_before = Pt(0)
        p_sum.paragraph_format.space_after = Pt(2.5 * spacing_scale)
        p_sum.paragraph_format.line_spacing = 1.08
        r_sum = p_sum.add_run(summary_text)
        r_sum.font.name = "Calibri"
        r_sum.font.size = Pt(8.7 * font_scale)
        r_sum.font.color.rgb = TEXT_DARK

    # ------------------ TECHNICAL COMPETENCIES ------------------
    skills_list = profile_data.get("technical_skills", [])
    if skills_list:
        add_section_header("Technical Skills & Core Competencies")
        t_skill = doc.add_table(rows=len(skills_list), cols=2)
        t_skill.autofit = False
        t_skill.columns[0].width = Inches(2.35)
        t_skill.columns[1].width = Inches(5.23)

        for i, item in enumerate(skills_list):
            cat = item.get("category", "") + ":"
            val = item.get("skills", "")
            row = t_skill.rows[i]
            c0, c1 = row.cells[0], row.cells[1]
            set_cell_margins(c0, top=2, bottom=2, left=4, right=8)
            set_cell_margins(c1, top=2, bottom=2, left=4, right=4)

            p0 = c0.paragraphs[0]
            p0.paragraph_format.space_before = Pt(0)
            p0.paragraph_format.space_after = Pt(0.8 * spacing_scale)
            r0 = p0.add_run(cat)
            r0.font.name = "Calibri"
            r0.font.size = Pt(8.5 * font_scale)
            r0.font.bold = True
            r0.font.color.rgb = PRIMARY

            p1 = c1.paragraphs[0]
            p1.paragraph_format.space_before = Pt(0)
            p1.paragraph_format.space_after = Pt(0.8 * spacing_scale)
            r1 = p1.add_run(val)
            r1.font.name = "Calibri"
            r1.font.size = Pt(8.5 * font_scale)
            r1.font.color.rgb = TEXT_DARK

    # ------------------ PROFESSIONAL EXPERIENCE ------------------
    work_list = profile_data.get("work_experience", [])
    if work_list:
        add_section_header("Professional Experience")
        for w_idx, work in enumerate(work_list):
            p_rw = doc.add_paragraph()
            p_rw.paragraph_format.space_before = Pt(1.8 * spacing_scale if w_idx > 0 else 1.2 * spacing_scale)
            p_rw.paragraph_format.space_after = Pt(1.0 * spacing_scale)
            p_rw.paragraph_format.keep_with_next = True

            r_title = p_rw.add_run(work.get("title", ""))
            r_title.font.name = "Calibri"
            r_title.font.size = Pt(9.3 * font_scale)
            r_title.font.bold = True
            r_title.font.color.rgb = PRIMARY

            r_comp = p_rw.add_run(f" | {work.get('company', '')}")
            r_comp.font.name = "Calibri"
            r_comp.font.size = Pt(9.1 * font_scale)
            r_comp.font.color.rgb = SECONDARY

            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_before = Pt(0)
            p_sub.paragraph_format.space_after = Pt(1.5 * spacing_scale)
            p_sub.paragraph_format.keep_with_next = True

            meta_parts = [work.get("location", ""), work.get("employment_type", ""), work.get("duration", "")]
            meta_str = "  |  ".join([p for p in meta_parts if p])
            r_meta = p_sub.add_run(meta_str)
            r_meta.font.name = "Calibri"
            r_meta.font.size = Pt(8.5 * font_scale)
            r_meta.font.color.rgb = MUTED

            for b in work.get("bullets", []):
                p_b = doc.add_paragraph()
                p_b.paragraph_format.left_indent = Inches(0.18)
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(1.3 * spacing_scale)
                p_b.paragraph_format.line_spacing = 1.07

                r_bullet = p_b.add_run("•  ")
                r_bullet.font.name = "Calibri"
                r_bullet.font.size = Pt(8.5 * font_scale)
                r_bullet.font.color.rgb = SECONDARY

                if isinstance(b, str):
                    prefix = ""
                    text_content = b
                else:
                    prefix = b.get("bold_prefix", "")
                    text_content = b.get("text", "")

                if prefix:
                    r_bold = p_b.add_run(prefix)
                    r_bold.font.name = "Calibri"
                    r_bold.font.size = Pt(8.5 * font_scale)
                    r_bold.font.bold = True
                    r_bold.font.color.rgb = PRIMARY

                r_txt = p_b.add_run(text_content)
                r_txt.font.name = "Calibri"
                r_txt.font.size = Pt(8.4 * font_scale)
                r_txt.font.color.rgb = TEXT_DARK

    # ------------------ FEATURED PROJECTS ------------------
    projects = profile_data.get("featured_projects") or profile_data.get("projects", [])
    if projects:
        add_section_header("Key Technical & Featured Projects")
        for p_idx, proj in enumerate(projects):
            p_proj = doc.add_paragraph()
            p_proj.paragraph_format.space_before = Pt(1.5 * spacing_scale)
            p_proj.paragraph_format.space_after = Pt(0.8 * spacing_scale)
            p_proj.paragraph_format.keep_with_next = True

            r_p_title = p_proj.add_run(proj.get("title", ""))
            r_p_title.font.name = "Calibri"
            r_p_title.font.size = Pt(9.1 * font_scale)
            r_p_title.font.bold = True
            r_p_title.font.color.rgb = PRIMARY

            stack = proj.get("tech_stack", "")
            if stack:
                r_p_tech = p_proj.add_run(f" | {stack}")
                r_p_tech.font.name = "Calibri"
                r_p_tech.font.size = Pt(8.5 * font_scale)
                r_p_tech.font.color.rgb = SECONDARY

            p_desc = doc.add_paragraph()
            p_desc.paragraph_format.left_indent = Inches(0.18)
            p_desc.paragraph_format.space_before = Pt(0)
            p_desc.paragraph_format.space_after = Pt(1.5 * spacing_scale)
            p_desc.paragraph_format.line_spacing = 1.07

            r_pb = p_desc.add_run("•  ")
            r_pb.font.name = "Calibri"
            r_pb.font.size = Pt(8.5 * font_scale)
            r_pb.font.color.rgb = SECONDARY

            r_ptxt = p_desc.add_run(proj.get("description", ""))
            r_ptxt.font.name = "Calibri"
            r_ptxt.font.size = Pt(8.4 * font_scale)
            r_ptxt.font.color.rgb = TEXT_DARK

            live_url = proj.get("live_url", "")
            if live_url:
                p_desc.add_run("  ")
                add_hyperlink(p_desc, live_url, "[View Project]", font_size=8.3 * font_scale, color_rgb=LINK_COLOR, bold=True)

    # ------------------ EDUCATION ------------------
    edu_list = profile_data.get("academic_background", [])
    if edu_list:
        add_section_header("Education")
        for edu in edu_list:
            p_edu = doc.add_paragraph()
            p_edu.paragraph_format.space_before = Pt(0)
            p_edu.paragraph_format.space_after = Pt(1.5 * spacing_scale)
            p_edu.paragraph_format.line_spacing = 1.07

            r_deg = p_edu.add_run(edu.get("degree", ""))
            r_deg.font.name = "Calibri"
            r_deg.font.size = Pt(9.1 * font_scale)
            r_deg.font.bold = True
            r_deg.font.color.rgb = PRIMARY

            r_inst = p_edu.add_run(f"  |  {edu.get('institution', '')}")
            r_inst.font.name = "Calibri"
            r_inst.font.size = Pt(8.7 * font_scale)
            r_inst.font.color.rgb = TEXT_DARK

            extra = [edu.get("duration", ""), edu.get("result", "")]
            extra_str = "  |  ".join([e for e in extra if e])
            if extra_str:
                r_res = p_edu.add_run(f"  |  {extra_str}")
                r_res.font.name = "Calibri"
                r_res.font.size = Pt(8.7 * font_scale)
                r_res.font.bold = True
                r_res.font.color.rgb = SECONDARY

    # ------------------ CERTIFICATIONS ------------------
    cert_list = profile_data.get("certifications", [])
    if cert_list:
        add_section_header("Professional Certifications")
        for cert in cert_list:
            p_c = doc.add_paragraph()
            p_c.paragraph_format.left_indent = Inches(0.18)
            p_c.paragraph_format.space_before = Pt(0)
            p_c.paragraph_format.space_after = Pt(1.0 * spacing_scale)
            p_c.paragraph_format.line_spacing = 1.07

            r_cb = p_c.add_run("•  ")
            r_cb.font.name = "Calibri"
            r_cb.font.size = Pt(8.5 * font_scale)
            r_cb.font.color.rgb = SECONDARY

            r_ct = p_c.add_run(f"{cert.get('name', '')} ({cert.get('issuer', '')})")
            r_ct.font.name = "Calibri"
            r_ct.font.size = Pt(8.5 * font_scale)
            r_ct.font.bold = True
            r_ct.font.color.rgb = PRIMARY

            v_url = cert.get("verify_url", "")
            if v_url:
                r_ct_sep = p_c.add_run("   |   ")
                r_ct_sep.font.name = "Calibri"
                r_ct_sep.font.size = Pt(8.5 * font_scale)
                r_ct_sep.font.color.rgb = MUTED
                add_hyperlink(p_c, v_url, "[Verify Credential]", font_size=8.4 * font_scale, color_rgb=LINK_COLOR, bold=True)

    # Sanitize document metadata to prevent tool leaks or OS username exposure
    core_props = doc.core_properties
    full_name = personal.get("full_name", "")
    core_props.author = full_name
    core_props.last_modified_by = full_name
    core_props.title = f"{full_name} - CV" if full_name else "Curriculum Vitae"
    core_props.comments = ""
    core_props.category = "Resume"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path)
    return output_path
