from src.config import Settings
from src.core.ingestion.metadata import Chunk
from src.providers.embeddings.local import HashEmbeddingProvider
from src.providers.llm.gateway import LLMGateway
from src.providers.vectorstore.memory_store import MemoryHybridStore
from src.services import RagService


async def test_chat_returns_citation():
    settings = Settings(relevance_threshold=0.0)
    embedder, store = HashEmbeddingProvider(64), MemoryHybridStore()
    service = RagService(settings, embedder, store, LLMGateway(None, None, None))
    chunk = Chunk("chunk-1", "parent-1", "doc-1", "acme", "Document: report; Page: 2. Aspirin dose is 75 mg daily.", "Aspirin dose is 75 mg daily.", 2, metadata={"filename": "report.pdf"})
    store.upsert([chunk], embedder.embed([chunk.text]))
    answer = await service.answer("What is the aspirin dose?", "acme", None)
    assert answer.citations[0].page == 2
    assert "75 mg" in answer.answer
