import asyncio
from pathlib import Path

from src.core.ingestion.chunker import chunk_pages
from src.core.ingestion.parser import extract_pages


async def ingest_document(service, document_id: str, path: Path) -> None:
    try:
        service.update_status(document_id, "parsing")
        pages = await asyncio.to_thread(extract_pages, path)
        service.update_status(document_id, "chunking", page_count=len(pages))
        document = service.get_document(document_id)
        chunks = chunk_pages(document_id, document.tenant_id, document.filename, pages, service.settings.chunk_size_words, service.settings.chunk_overlap_words)
        service.update_status(document_id, "indexing", chunk_count=len(chunks))
        vectors = await asyncio.to_thread(service.embedder.embed, [chunk.text for chunk in chunks])
        await asyncio.to_thread(service.store.upsert, chunks, vectors)
        service.update_status(document_id, "indexed")
    except Exception as exc:
        service.update_status(document_id, "failed", error=str(exc))
