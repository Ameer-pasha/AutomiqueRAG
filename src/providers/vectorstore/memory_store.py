from src.core.ingestion.metadata import Chunk


class MemoryHybridStore:
    def __init__(self) -> None:
        self.entries: list[tuple[Chunk, list[float]]] = []

    def upsert(self, chunks, vectors) -> None:
        self.entries.extend(zip(chunks, vectors, strict=True))

    def search(self, vector, tenant_id, document_ids, limit):
        ranked = []
        for chunk, stored in self.entries:
            if chunk.tenant_id == tenant_id and (not document_ids or chunk.document_id in document_ids):
                ranked.append((chunk, sum(left * right for left, right in zip(vector, stored, strict=True))))
        return sorted(ranked, key=lambda item: item[1], reverse=True)[:limit]

    def delete_document(self, document_id, tenant_id) -> None:
        self.entries = [item for item in self.entries if not (item[0].document_id == document_id and item[0].tenant_id == tenant_id)]
