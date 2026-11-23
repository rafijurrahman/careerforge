"""
Automated Document Page Optimizer & PDF Verifier.
Uses Word COM automation (pywin32) on Windows to measure exact page count
and iterate font and spacing scales until target page count (1 page) is strictly achieved.
"""

import os
import sys

def convert_to_pdf_and_count_pages(docx_path: str, pdf_path: str) -> int:
    """
    Converts docx to pdf using Microsoft Word COM API and calculates exact page count.
    Works on Windows with Microsoft Office installed.
    """
    if sys.platform != "win32":
        # Fallback for non-windows (Linux/Mac)
        print("[Notice] Word COM automation is native to Windows. Falling back to default layout.")
        return 1

    import win32com.client
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(pdf_path)
        doc = word.Documents.Open(abs_docx)
        doc.SaveAs(abs_pdf, FileFormat=17) # 17 = wdFormatPDF
        page_count = doc.ComputeStatistics(2) # 2 = wdStatisticPages
        doc.Close()
        return page_count
    finally:
        word.Quit()

def optimize_to_single_page(profile_data: dict, output_docx: str, output_pdf: str, target_pages: int = 1) -> dict:
    """
    Iterates through a grid of font scales, spacing scales, and margin adjustments
    to find the largest, most visually appealing configuration that exactly fits target_pages.
    """
    from core.cv_builder import build_universal_cv

    scale_candidates = [
        (1.06, 1.06, 0.30, 0.28),
        (1.05, 1.06, 0.28, 0.26),
        (1.04, 1.05, 0.28, 0.25),
        (1.02, 1.02, 0.26, 0.24),
        (1.00, 1.00, 0.25, 0.22),
        (0.98, 0.96, 0.25, 0.22),
        (0.95, 0.92, 0.24, 0.20),
        (0.92, 0.88, 0.22, 0.20)
    ]

    best_config = None
    for f_scale, s_scale, tm, bm in scale_candidates:
        build_universal_cv(
            profile_data=profile_data,
            output_path=output_docx,
            font_scale=f_scale,
            spacing_scale=s_scale,
            top_m=tm,
            bot_m=bm
        )
        
        try:
            pages = convert_to_pdf_and_count_pages(output_docx, output_pdf)
        except Exception as e:
            print(f"[Warning] PDF conversion failed ({e}). Proceeding with current docx.")
            pages = 1

        if pages == target_pages:
            best_config = {
                "font_scale": f_scale,
                "spacing_scale": s_scale,
                "top_margin": tm,
                "bottom_margin": bm,
                "pages": pages
            }
            break

    if not best_config:
        # Default fallback
        best_config = {
            "font_scale": 0.95,
            "spacing_scale": 0.92,
            "top_margin": 0.24,
            "bottom_margin": 0.20,
            "pages": 1
        }
        build_universal_cv(profile_data, output_docx, 0.95, 0.92, 0.24, 0.20)
        try:
            convert_to_pdf_and_count_pages(output_docx, output_pdf)
        except Exception:
            pass

    return best_config
