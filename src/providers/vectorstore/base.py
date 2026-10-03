from collections.abc import Iterable
from typing import Protocol

from src.core.ingestion.metadata import Chunk


class VectorStore(Protocol):
    def upsert(self, chunks: Iterable[Chunk], vectors: Iterable[list[float]]) -> None: ...
    def search(self, vector: list[float], tenant_id: str, document_ids: set[str] | None, limit: int) -> list[tuple[Chunk, float]]: ...
    def delete_document(self, document_id: str, tenant_id: str) -> None: ...
