from pathlib import Path

from src.config import Settings
from src.core.ingestion import pipeline
from src.providers.embeddings.local import HashEmbeddingProvider
from src.providers.llm.gateway import LLMGateway
from src.providers.vectorstore.memory_store import MemoryHybridStore
from src.services import RagService


async def test_scanned_ingestion_keeps_original_page_for_citation(monkeypatch):
    settings = Settings(relevance_threshold=0.0)
    embedder, store = HashEmbeddingProvider(64), MemoryHybridStore()
    service = RagService(settings, embedder, store, LLMGateway(None, None, None))
    document = service.create_document("scanned.pdf", "acme")
    monkeypatch.setattr(pipeline, "extract_pages", lambda path: ["", "OCR says the dose is 75 mg daily."])

    await pipeline.ingest_document(service, document.id, Path("tests/fixtures/scanned.pdf"))

    indexed = service.get_document(document.id)
    assert indexed.status == "indexed"
    answer = await service.answer("What dose?", "acme", [document.id])
    assert answer.citations[0].page == 2