def needs_ocr(page_text: str) -> bool:
    return len(page_text.strip()) < 20
