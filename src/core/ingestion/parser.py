from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pypdf import PdfReader

from src.core.ingestion.scanned import OCRExtractionError, extract_ocr_pages, needs_ocr


class DocumentExtractionError(ValueError):
    """Raised when neither text extraction nor OCR produces usable pages."""


def _is_text_based_pdf(path: Path, min_chars: int = 50, sample_pages: int = 3) -> bool:
    """Fast check: if first N pages have enough selectable text, skip ML parsers."""
    try:
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages[:sample_pages]):
            if len((page.extract_text() or "").strip()) < min_chars:
                return False
        return True
    except Exception:
        return False


def extract_pages(
    path: Path,
    docling_device: str | None = None,
    mineru_device: str | None = None,
    fast_path: bool = True,
    fast_path_min_chars: int = 50,
    fast_path_sample_pages: int = 3,
    mineru_formula_enable: bool = True,
    mineru_table_enable: bool = True,
    docling_images_scale: float = 1.0,
    parallel_workers: int = 4,
) -> list[str]:
    """Extract page-preserving Markdown with MinerU -> Docling -> pypdf fallback chain.

    Layer 0 (fast-path): Quick pypdf check — if text-rich, use pypdf directly.
    Layer 1: MinerU (primary) — best layout/table/formula extraction.
    Layer 2: Docling (first fallback) — layout-aware Markdown without OCR.
    Layer 3: pypdf (final fallback) — basic text extraction.

    When pages have little text, OCR replaces only those pages; page indexes
    remain aligned with the original PDF for citations.
    """
    # Layer 0: Fast-path for text-based PDFs
    if fast_path and _is_text_based_pdf(path, fast_path_min_chars, fast_path_sample_pages):
        return _extract_pypdf_pages(path)

    # Layer 1: MinerU (primary)
    try:
        pages = _extract_mineru_pages(
            path,
            device=mineru_device,
            formula_enable=mineru_formula_enable,
            table_enable=mineru_table_enable,
            parallel_workers=parallel_workers,
        )
    except Exception:
        # Layer 2: Docling (first fallback)
        try:
            pages = _extract_docling_pages(
                path,
                device=docling_device,
                images_scale=docling_images_scale,
            )
        except Exception:
            # Layer 3: pypdf (second fallback)
            pages = _extract_pypdf_pages(path)

    missing_pages = [index for index, text in enumerate(pages) if needs_ocr(text)]
    if not missing_pages:
        return pages

    try:
        ocr_pages = extract_ocr_pages(path, docling_device)
    except OCRExtractionError as exc:
        page_numbers = ", ".join(str(page + 1) for page in missing_pages)
        raise DocumentExtractionError(
            f"Pages {page_numbers} have no selectable text and OCR failed: {exc}"
        ) from exc

    if len(ocr_pages) != len(pages):
        raise DocumentExtractionError("OCR returned a different number of pages than the source PDF.")
    unresolved = [index for index in missing_pages if needs_ocr(ocr_pages[index])]
    if unresolved:
        page_numbers = ", ".join(str(page + 1) for page in unresolved)
        raise DocumentExtractionError(f"OCR did not produce usable text for pages {page_numbers}.")
    for index in missing_pages:
        pages[index] = ocr_pages[index]
    return pages


def _extract_mineru_pages(
    path: Path,
    device: str | None = None,
    formula_enable: bool = True,
    table_enable: bool = True,
    parallel_workers: int = 4,
) -> list[str]:
    """Use MinerU for PDF parsing with layout/table/formula extraction."""
    try:
        from mineru.cli import parse_pdf
    except ImportError:
        raise ImportError("MinerU is not installed. Install with: pip install mineru")

    import tempfile
    from pathlib import Path as PathLib

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            output_dir = parse_pdf(
                pdf_path=str(path),
                output_dir=tmpdir,
                lang="auto",
                device=device or "cpu",
                formula_enable=formula_enable,
                table_enable=table_enable,
            )
        except Exception as e:
            raise RuntimeError(f"MinerU parsing failed: {e}") from e

        md_files = list(PathLib(output_dir).rglob("*.md"))
        if not md_files:
            raise RuntimeError("MinerU did not produce markdown output.")

        md_content = md_files[0].read_text(encoding="utf-8")

        pages = []
        current_page = []
        for line in md_content.split("\n"):
            if line.startswith("## Page ") or line.startswith("# Page "):
                if current_page:
                    pages.append("\n".join(current_page).strip())
                current_page = [line]
            else:
                current_page.append(line)
        if current_page:
            pages.append("\n".join(current_page).strip())

        if not pages:
            pages = [md_content.strip()]

        if not pages or not any(pages):
            raise ValueError("MinerU did not return any usable content.")

        return pages


def _extract_docling_pages(
    path: Path,
    device: str | None = None,
    images_scale: float = 1.0,
) -> list[str]:
    """Use Docling's layout/table-aware Markdown export without OCR."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    options = PdfPipelineOptions()
    options.do_ocr = False
    if device:
        options.device = device
    if images_scale != 1.0:
        options.images_scale = images_scale
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


def extract_digital_pages(
    path: Path,
    docling_device: str | None = None,
    mineru_device: str | None = None,
    fast_path: bool = True,
    fast_path_min_chars: int = 50,
    fast_path_sample_pages: int = 3,
    mineru_formula_enable: bool = True,
    mineru_table_enable: bool = True,
    docling_images_scale: float = 1.0,
    parallel_workers: int = 4,
) -> list[str]:
    """Backward-compatible name for callers that expect the ingestion parser."""
    return extract_pages(
        path,
        docling_device=docling_device,
        mineru_device=mineru_device,
        fast_path=fast_path,
        fast_path_min_chars=fast_path_min_chars,
        fast_path_sample_pages=fast_path_sample_pages,
        mineru_formula_enable=mineru_formula_enable,
        mineru_table_enable=mineru_table_enable,
        docling_images_scale=docling_images_scale,
        parallel_workers=parallel_workers,
    )