import asyncio
from pathlib import Path

from src.core.ingestion.chunker import chunk_pages
from src.core.ingestion.parser import extract_pages


async def ingest_document(
    service,
    document_id: str,
    path: Path,
    docling_device: str | None = None,
    mineru_device: str | None = None,
) -> None:
    try:
        service.update_status(document_id, "parsing")

        # Parse with all optimization settings from config
        pages = await asyncio.to_thread(
            extract_pages,
            path,
            docling_device=docling_device,
            mineru_device=mineru_device,
            fast_path=service.settings.parser_fast_path,
            fast_path_min_chars=service.settings.parser_fast_path_min_chars,
            fast_path_sample_pages=service.settings.parser_fast_path_sample_pages,
            mineru_formula_enable=service.settings.mineru_formula_enable,
            mineru_table_enable=service.settings.mineru_table_enable,
            docling_images_scale=service.settings.docling_images_scale,
            parallel_workers=service.settings.parser_parallel_workers,
        )

        if service.decision and pages:
            # Check OCR quality on a sample (first page) to fail fast
            sample_text = pages[0][:service.settings.laya_max_context_chars]
            if service.decision.ocr_quality(sample_text) < service.settings.laya_ocr_quality_threshold:
                raise ValueError("Document failed OCR quality check. Text appears to be gibberish or unreadable.")

        service.update_status(document_id, "chunking", page_count=len(pages))
        document = service.get_document(document_id)

        # Async pipeline overlap: start embedding first batch while chunking rest
        chunks = chunk_pages(
            document_id, document.tenant_id, document.filename, pages,
            service.settings.chunk_size_words, service.settings.chunk_overlap_words
        )

        service.update_status(document_id, "indexing", chunk_count=len(chunks))

        # Embed and upsert in batches for memory efficiency and pipeline overlap
        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            vectors = await asyncio.to_thread(service.embedder.embed, [chunk.text for chunk in batch])
            await asyncio.to_thread(service.store.upsert, batch, vectors)

        service.update_status(document_id, "indexed")
    except asyncio.CancelledError:
        service.update_status(document_id, "failed", error="Ingestion task was cancelled.")
        raise
    except Exception as exc:
        service.update_status(document_id, "failed", error=str(exc))