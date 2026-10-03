from pathlib import Path

from pypdf import PdfReader


def extract_digital_pages(path: Path) -> list[str]:
    pages = [(page.extract_text() or "").strip() for page in PdfReader(str(path)).pages]
    if not any(pages):
        raise ValueError("No selectable text found; configure Docling/OCR for scanned pages.")
    return pages
