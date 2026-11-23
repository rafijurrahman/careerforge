"""
Automated Document Page Optimizer & PDF Verifier.
Supports LibreOffice headless (cross-platform default) and Microsoft Word COM (Windows fast-path).
Iterates font, margin, and spacing scales until target page count (1 page) is strictly achieved.
"""

import os
import re
import shutil
import subprocess
import sys
from typing import Optional, Tuple


def count_pdf_pages(pdf_path: str) -> int:
    """Calculates page count from a generated PDF file."""
    if not os.path.exists(pdf_path):
        return 1

    # Method 1: pypdf if available
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        pass

    # Method 2: Fast regex inspection of PDF structure
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
            # Count /Type /Page objects (excluding /Pages catalog)
            matches = re.findall(rb"/Type\s*/Page(?=[^s]|$)", content)
            if matches:
                return len(matches)
    except Exception:
        pass

    return 1


def convert_with_word_com(docx_path: str, output_pdf: str) -> Optional[int]:
    """Converts docx to PDF via Microsoft Word COM (Windows fast-path). Returns page count."""
    if sys.platform != "win32":
        return None

    try:
        import win32com.client
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        try:
            abs_docx = os.path.abspath(docx_path)
            abs_pdf = os.path.abspath(output_pdf)
            doc = word.Documents.Open(abs_docx)
            doc.SaveAs(abs_pdf, FileFormat=17)  # 17 = wdFormatPDF
            pages = int(doc.ComputeStatistics(2))  # 2 = wdStatisticPages
            doc.Close(SaveChanges=False)
            return pages
        finally:
            try:
                word.Quit()
            except Exception:
                pass
    except Exception:
        return None


def find_libreoffice_bin() -> Optional[str]:
    """Finds the LibreOffice soffice binary across PATH and standard install directories."""
    # 1. Check PATH
    bin_path = shutil.which("soffice") or shutil.which("libreoffice")
    if bin_path:
        return bin_path

    # 2. Check standard Windows directories
    if sys.platform == "win32":
        standard_windows_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\LibreOffice\program\soffice.exe"),
        ]
        for p in standard_windows_paths:
            if os.path.exists(p):
                return p

    # 3. Check standard macOS directories
    if sys.platform == "darwin":
        mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if os.path.exists(mac_path):
            return mac_path

    return None


def convert_with_libreoffice(docx_path: str, output_pdf: str) -> Optional[int]:
    """Converts docx to PDF via headless LibreOffice (cross-platform default)."""
    libre_bin = find_libreoffice_bin()
    if not libre_bin:
        return None

    abs_docx = os.path.abspath(docx_path)
    abs_pdf = os.path.abspath(output_pdf)
    out_dir = os.path.dirname(abs_pdf) or "."

    try:
        proc = subprocess.run(
            [
                libre_bin,
                "--headless",
                "--convert-to",
                "pdf:writer_pdf_Export",
                "--outdir",
                out_dir,
                abs_docx,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
            check=False,
        )
        if proc.returncode == 0:
            # LibreOffice names the output based on the input filename
            base_name = os.path.splitext(os.path.basename(abs_docx))[0]
            generated_pdf = os.path.join(out_dir, f"{base_name}.pdf")
            if generated_pdf != abs_pdf and os.path.exists(generated_pdf):
                shutil.move(generated_pdf, abs_pdf)
            if os.path.exists(abs_pdf):
                return count_pdf_pages(abs_pdf)
    except Exception:
        pass

    return None


def convert_to_pdf_and_count_pages(docx_path: str, pdf_path: str, engine: str = "auto") -> Tuple[int, str]:
    """
    Converts docx to PDF and computes page count according to specified engine.
    Engines:
      - 'auto': Windows uses Word COM if available, else LibreOffice; macOS uses LibreOffice.
      - 'word': Forces Microsoft Word COM (Windows only).
      - 'libreoffice': Forces LibreOffice headless.
    """
    engine_lower = (engine or "auto").lower()

    if engine_lower == "word":
        if sys.platform != "win32":
            raise RuntimeError("Engine 'word' (Microsoft Word COM) is only supported on Windows.")
        pages = convert_with_word_com(docx_path, pdf_path)
        if pages is None:
            raise RuntimeError("Word COM engine failed. Ensure Microsoft Word is installed and pywin32 is available.")
        return pages, "Word COM"

    if engine_lower == "libreoffice":
        pages = convert_with_libreoffice(docx_path, pdf_path)
        if pages is None:
            hint = "winget install TheDocumentFoundation.LibreOffice"
            if sys.platform == "darwin":
                hint = "brew install --cask libreoffice"
            elif sys.platform.startswith("linux"):
                hint = "sudo apt-get install -y libreoffice-writer"
            raise RuntimeError(f"LibreOffice not found or conversion failed. Install it via: {hint}")
        return pages, "LibreOffice Headless"

    # 'auto' mode
    if sys.platform.startswith("linux"):
        print("[Info] Linux is community-supported; page-fit is best-effort.", file=sys.stderr)

    # On Windows, try Word COM first (fast-path)
    if sys.platform == "win32":
        pages = convert_with_word_com(docx_path, pdf_path)
        if pages is not None:
            return pages, "Word COM"

    # Otherwise (or if Word COM unavailable on Windows), try LibreOffice
    pages = convert_with_libreoffice(docx_path, pdf_path)
    if pages is not None:
        return pages, "LibreOffice Headless"

    return 1, "None (install LibreOffice or Word for exact PDF page verification)"


def optimize_to_single_page(
    profile_data: dict, output_docx: str, output_pdf: str, target_pages: int = 1, engine: str = "auto"
) -> dict:
    """
    Iterates through font scales and margins to find the best configuration fitting target_pages.
    """
    try:
        from careerforge.core.cv_builder import build_universal_cv
    except ImportError:
        from core.cv_builder import build_universal_cv

    scale_candidates = [
        (1.06, 1.06, 0.30, 0.28),
        (1.05, 1.06, 0.28, 0.26),
        (1.04, 1.05, 0.28, 0.25),
        (1.02, 1.02, 0.26, 0.24),
        (1.00, 1.00, 0.25, 0.22),
        (0.98, 0.96, 0.25, 0.22),
        (0.95, 0.92, 0.24, 0.20),
        (0.92, 0.88, 0.22, 0.20),
    ]

    best_config = None
    last_backend = "Unknown"

    for font_s, space_s, top_m, bottom_m in scale_candidates:
        build_universal_cv(
            profile_data,
            output_docx,
            font_scale=font_s,
            spacing_scale=space_s,
            top_m=top_m,
            bot_m=bottom_m,
        )

        pages, backend = convert_to_pdf_and_count_pages(output_docx, output_pdf, engine=engine)
        last_backend = backend

        if backend.startswith("None"):
            # Can't count pages without a PDF backend; stop at standard scale
            best_config = {
                "font_scale": 1.0,
                "spacing_scale": 1.0,
                "margin_top": 0.25,
                "margin_bottom": 0.22,
                "pages": 1,
                "backend": backend,
            }
            break

        if pages == target_pages:
            best_config = {
                "font_scale": font_s,
                "spacing_scale": space_s,
                "margin_top": top_m,
                "margin_bottom": bottom_m,
                "pages": pages,
                "backend": backend,
            }
            break

    if not best_config:
        best_config = {
            "font_scale": scale_candidates[-1][0],
            "spacing_scale": scale_candidates[-1][1],
            "margin_top": scale_candidates[-1][2],
            "margin_bottom": scale_candidates[-1][3],
            "pages": 1,
            "backend": last_backend,
        }

    return best_config
