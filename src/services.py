import asyncio
import uuid
from datetime import UTC, datetime

from src.config import Settings
from src.core.cache.semantic_cache import SemanticCache
from src.core.generation.citations import citations_for
from src.core.generation.generator import generate
from src.core.guard.relevance_gate import has_relevant_context
from src.core.ingestion.pipeline import ingest_document
from src.core.retrieval.context import build_context
from src.core.retrieval.hybrid import hybrid_search
from src.core.retrieval.query_rewrite import rewrite_query
from src.schemas.chat import ChatResponse
from src.schemas.document import DocumentResponse, DocumentStatus


class RagService:
    def __init__(self, settings: Settings, embedder, store, llm) -> None:
        self.settings, self.embedder, self.store, self.llm = settings, embedder, store, llm
        self.documents: dict[str, DocumentResponse] = {}
        self.cache, self.feedback = SemanticCache(), []

    def create_document(self, filename: str, tenant_id: str) -> DocumentResponse:
        document = DocumentResponse(id=str(uuid.uuid4()), filename=filename, tenant_id=tenant_id, status=DocumentStatus.queued, created_at=datetime.now(UTC))
        self.documents[document.id] = document
        return document

    def get_document(self, document_id: str) -> DocumentResponse:
        return self.documents[document_id]

    def update_status(self, document_id: str, status: str, **updates) -> None:
        self.documents[document_id] = self.documents[document_id].model_copy(update={"status": DocumentStatus(status), **updates})

    def enqueue_ingestion(self, document_id, path) -> None:
        asyncio.create_task(ingest_document(self, document_id, path))

    async def answer(self, query: str, tenant_id: str, document_ids: list[str] | None) -> ChatResponse:
        rewritten = rewrite_query(query)
        vector = (await asyncio.to_thread(self.embedder.embed, [rewritten]))[0]
        cached = self.cache.get(vector, tenant_id, self.settings.semantic_cache_threshold)
        if cached:
            return cached.model_copy(update={"cached": True})
        dense, fused = await asyncio.to_thread(hybrid_search, self.store, rewritten, vector, tenant_id, set(document_ids) if document_ids else None, self.settings.retrieval_candidates)
        if not has_relevant_context(dense, self.settings.relevance_threshold):
            return ChatResponse(answer="I could not find enough relevant information in the selected documents.", citations=[], abstained=True)
        context = build_context(fused, self.settings.final_context_chunks)
        response = ChatResponse(answer=await generate(self.llm, rewritten, context), citations=citations_for(context))
        self.cache.put(vector, tenant_id, response)
        return response
