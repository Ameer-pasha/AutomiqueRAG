import uuid

from src.core.ingestion.metadata import Chunk


def chunk_pages(document_id: str, tenant_id: str, filename: str, pages: list[str], size: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    for page, text in enumerate(pages, start=1):
        words = text.split()
        section = next((line.strip() for line in text.splitlines() if line.strip()), "Document")[:160]
        for start in range(0, len(words), step):
            child = words[start : start + size]
            if not child:
                continue
            parent = words[max(0, start - overlap) : min(len(words), start + size + overlap)]
            header = f"Document: {filename}; Section: {section}; Page: {page}. "
            chunks.append(Chunk(str(uuid.uuid4()), f"{document_id}:{page}:{start}", document_id, tenant_id, header + " ".join(child), " ".join(parent), page, section, {"filename": filename, "page": page}))
    return chunks
