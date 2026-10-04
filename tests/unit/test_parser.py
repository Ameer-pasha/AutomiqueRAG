from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from src.core.ingestion import parser
from src.core.ingestion.scanned import OCRExtractionError
from src.core.ingestion.validator import validate_pdf


def test_docling_pages_are_kept_in_original_order(monkeypatch):
    monkeypatch.setattr(parser, "_extract_docling_pages", lambda path: ["# Page one\nDigital text", "# Page two\nTable text"])

    assert parser.extract_pages(Path("tests/fixtures/digital.pdf")) == [
        "# Page one\nDigital text",
        "# Page two\nTable text",
    ]


def test_scanned_page_is_replaced_by_ocr_text(monkeypatch):
    monkeypatch.setattr(parser, "_extract_docling_pages", lambda path: ["Digital page has enough selectable text", ""])
    monkeypatch.setattr(parser, "extract_ocr_pages", lambda path: ["Digital page has enough selectable text", "OCR text from original page two"])

    assert parser.extract_pages(Path("tests/fixtures/scanned.pdf")) == [
        "Digital page has enough selectable text",
        "OCR text from original page two",
    ]


def test_scanned_page_reports_ocr_failure(monkeypatch):
    monkeypatch.setattr(parser, "_extract_docling_pages", lambda path: [""])

    def fail_ocr(path):
        raise OCRExtractionError("engine unavailable")

    monkeypatch.setattr(parser, "extract_ocr_pages", fail_ocr)
    with pytest.raises(parser.DocumentExtractionError, match="Pages 1.*OCR failed"):
        parser.extract_pages(Path("tests/fixtures/scanned.pdf"))


async def test_invalid_non_pdf_upload_is_rejected():
    upload = UploadFile(filename="not-a-pdf.txt", file=__import__("io").BytesIO(b"not a PDF"))
    with pytest.raises(HTTPException, match="Only PDF uploads"):
        await validate_pdf(upload, 50)
