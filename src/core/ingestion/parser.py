from pathlib import Path

from pypdf import PdfReader

from src.core.ingestion.scanned import OCRExtractionError, extract_ocr_pages, needs_ocr


class DocumentExtractionError(ValueError):
    """Raised when neither text extraction nor OCR produces usable pages."""


def extract_pages(path: Path) -> list[str]:
    """Extract page-preserving Markdown with Docling, falling back to pypdf.

    Docling is used without OCR first so digital PDFs avoid OCR cost. When one
    or more pages have little text, OCR replaces only those pages; page indexes
    remain aligned with the original PDF for citations.
    """
    try:
        pages = _extract_docling_pages(path)
    except Exception:
        pages = _extract_pypdf_pages(path)

    missing_pages = [index for index, text in enumerate(pages) if needs_ocr(text)]
    if not missing_pages:
        return pages

    try:
        ocr_pages = extract_ocr_pages(path)
    except OCRExtractionError as exc:
        page_numbers = ", ".join(str(page + 1) for page in missing_pages)
        raise DocumentExtractionError(
            f"Pages {page_numbers} have no selectable text and OCR failed: {exc}"
        ) from exc

    if len(ocr_pages) != len(pages):
        raise DocumentExtractionError("Docling OCR returned a different number of pages than the source PDF.")
    unresolved = [index for index in missing_pages if needs_ocr(ocr_pages[index])]
    if unresolved:
        page_numbers = ", ".join(str(page + 1) for page in unresolved)
        raise DocumentExtractionError(f"OCR did not produce usable text for pages {page_numbers}.")
    for index in missing_pages:
        pages[index] = ocr_pages[index]
    return pages


def _extract_docling_pages(path: Path) -> list[str]:
    """Use Docling's layout/table-aware Markdown export without OCR."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )
    document = converter.convert(path).document
    pages = [
        document.export_to_markdown(page_no=page_no).strip()
        for page_no in range(1, len(document.pages) + 1)
    ]
    if not pages:
        raise ValueError("Docling did not return any PDF pages.")
    return pages


def _extract_pypdf_pages(path: Path) -> list[str]:
    pages = [(page.extract_text() or "").strip() for page in PdfReader(str(path)).pages]
    if not pages:
        raise DocumentExtractionError("The PDF has no pages.")
    return pages


def extract_digital_pages(path: Path) -> list[str]:
    """Backward-compatible name for callers that expect the ingestion parser."""
    return extract_pages(path)
