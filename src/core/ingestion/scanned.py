from pathlib import Path


class OCRExtractionError(RuntimeError):
    """Raised when image-only PDF pages cannot be converted to text."""


def needs_ocr(page_text: str) -> bool:
    """Return whether a page lacks enough text to be useful for retrieval."""
    return len(page_text.strip()) < 20


def extract_ocr_pages(path: Path) -> list[str]:
    """Convert a PDF with Docling's built-in OCR and retain original page order."""
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError as exc:
        raise OCRExtractionError(
            "Scanned pages require Docling OCR. Install the project's Docling dependency and its OCR extras."
        ) from exc

    try:
        options = PdfPipelineOptions()
        options.do_ocr = True
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
        )
        document = converter.convert(path).document
        return [
            document.export_to_markdown(page_no=page_no).strip()
            for page_no in range(1, len(document.pages) + 1)
        ]
    except Exception as exc:
        raise OCRExtractionError(f"Docling OCR failed for '{path.name}': {exc}") from exc
