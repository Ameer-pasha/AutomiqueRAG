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
    def __init__(self, settings: Settings, embedder, store, llm, documents=None) -> None:
        self.settings, self.embedder, self.store, self.llm = settings, embedder, store, llm
        self.document_repository = documents
        self.documents = {document.id: document for document in documents.list_all()} if documents else {}
        self.cache, self.feedback = SemanticCache(), []

    def create_document(self, filename: str, tenant_id: str) -> DocumentResponse:
        document = DocumentResponse(id=str(uuid.uuid4()), filename=filename, tenant_id=tenant_id, status=DocumentStatus.queued, created_at=datetime.now(UTC))
        self.documents[document.id] = document
        if self.document_repository:
            self.document_repository.save(document)
        return document

    def get_document(self, document_id: str) -> DocumentResponse:
        return self.documents[document_id]

    def update_status(self, document_id: str, status: str, **updates) -> None:
        document = self.documents[document_id].model_copy(update={"status": DocumentStatus(status), **updates})
        self.documents[document_id] = document
        if self.document_repository:
            self.document_repository.save(document)

    def delete_document(self, document_id: str, tenant_id: str) -> None:
        self.store.delete_document(document_id, tenant_id)
        self.documents.pop(document_id)
        if self.document_repository:
            self.document_repository.delete(document_id)

    def enqueue_ingestion(self, document_id, path) -> None:
        asyncio.create_task(ingest_document(self, document_id, path))

    def enqueue_reindex(self, document_id: str) -> None:
        document = self.get_document(document_id)
        source = self.settings.upload_dir / document.tenant_id / f"{document_id}.pdf"
        self.store.delete_document(document_id, document.tenant_id)
        asyncio.create_task(ingest_document(self, document_id, source))

    async def answer(self, query: str, tenant_id: str, document_ids: list[str] | None) -> ChatResponse:
        rewritten = rewrite_query(query)
        vector = (await asyncio.to_thread(self.embedder.embed, [rewritten]))[0]
        cached = self.cache.get(vector, tenant_id, self.settings.semantic_cache_threshold)
        if cached:
            return cached.model_copy(update={"cached": True})
        dense, fused = await asyncio.to_thread(hybrid_search, self.store, rewritten, vector, tenant_id, set(document_ids) if document_ids else None, self.settings.retrieval_candidates)
        if not has_relevant_context(dense, self.settings.relevance_threshold):
            return ChatResponse(answer="I could not find enough relevant information in the selected documents.", citations=[], abstained=True)
        context = build_context(fused, self.settings.llm_context_chunks)
        response = ChatResponse(answer=await generate(self.llm, rewritten, context), citations=citations_for(context))
        self.cache.put(vector, tenant_id, response)
        return response
