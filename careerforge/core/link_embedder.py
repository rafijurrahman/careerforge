"""
Hyperlink helper module for python-docx documents.
Embeds genuine clickable hyperlinks with custom styling into paragraphs.
"""

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def add_hyperlink(paragraph, url, text, font_name="Calibri", font_size=8.5, color_rgb=(2, 132, 199), bold=False, underline=False):
    """
    Inserts a clickable external hyperlink into a python-docx paragraph.

    :param paragraph: Target docx paragraph
    :param url: Destination URL string
    :param text: Visible anchor text
    :param font_name: Font typeface name
    :param font_size: Font size in Points
    :param color_rgb: Tuple of (R, G, B) integers
    :param bold: Boolean flag for bold weight
    :param underline: Boolean flag for underline
    """
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    if font_name:
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rPr.append(rFonts)

    if font_size:
        sz = OxmlElement('w:sz')
        sz.set(qn('w:val'), str(int(font_size * 2)))
        rPr.append(sz)

    if bold:
        b = OxmlElement('w:b')
        rPr.append(b)

    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)

    if color_rgb:
        color = OxmlElement('w:color')
        hex_color = f"{color_rgb[0]:02X}{color_rgb[1]:02X}{color_rgb[2]:02X}"
        color.set(qn('w:val'), hex_color)
        rPr.append(color)

    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return hyperlink
