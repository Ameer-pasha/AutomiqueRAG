import json

from src.core.ingestion.metadata import Chunk
from src.db.session import connect


class SQLiteHybridStore:
    """Persistent local vector store for development; Qdrant is the production replacement."""

    def __init__(self, database_path) -> None:
        self.database_path = database_path
        with connect(database_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY, parent_id TEXT NOT NULL, document_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL, text TEXT NOT NULL, parent_text TEXT NOT NULL,
                    page INTEGER NOT NULL, section_path TEXT NOT NULL, metadata_json TEXT NOT NULL,
                    vector_json TEXT NOT NULL
                )
            """)
            connection.execute("CREATE INDEX IF NOT EXISTS idx_chunks_tenant_document ON chunks (tenant_id, document_id)")

    def upsert(self, chunks, vectors) -> None:
        rows = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            rows.append((chunk.id, chunk.parent_id, chunk.document_id, chunk.tenant_id, chunk.text, chunk.parent_text, chunk.page, chunk.section_path, json.dumps(chunk.metadata), json.dumps(vector)))
        with connect(self.database_path) as connection:
            connection.executemany("""
                INSERT INTO chunks (id, parent_id, document_id, tenant_id, text, parent_text, page, section_path, metadata_json, vector_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET text=excluded.text, parent_text=excluded.parent_text, vector_json=excluded.vector_json
            """, rows)

    def search(self, vector, tenant_id, document_ids, limit):
        query = "SELECT * FROM chunks WHERE tenant_id = ?"
        parameters: list[str] = [tenant_id]
        if document_ids:
            placeholders = ", ".join("?" for _ in document_ids)
            query += f" AND document_id IN ({placeholders})"
            parameters.extend(document_ids)
        with connect(self.database_path) as connection:
            rows = connection.execute(query, parameters).fetchall()
        scored = []
        for row in rows:
            stored_vector = json.loads(row["vector_json"])
            chunk = Chunk(row["id"], row["parent_id"], row["document_id"], row["tenant_id"], row["text"], row["parent_text"], row["page"], row["section_path"], json.loads(row["metadata_json"]))
            if len(vector) == len(stored_vector):
                scored.append((chunk, sum(left * right for left, right in zip(vector, stored_vector, strict=True))))
        return sorted(scored, key=lambda item: item[1], reverse=True)[:limit]

    def delete_document(self, document_id, tenant_id) -> None:
        with connect(self.database_path) as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ? AND tenant_id = ?", (document_id, tenant_id))
