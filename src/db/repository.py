from datetime import datetime

from src.db.session import connect
from src.schemas.document import DocumentResponse, DocumentStatus


class DocumentRepository:
    def __init__(self, database_path) -> None:
        self.database_path = database_path
        with connect(database_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, tenant_id TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL, page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL, error TEXT
                )
            """)

    def save(self, document: DocumentResponse) -> None:
        with connect(self.database_path) as connection:
            connection.execute("""
                INSERT INTO documents (id, filename, tenant_id, status, created_at, page_count, chunk_count, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status, page_count=excluded.page_count,
                    chunk_count=excluded.chunk_count, error=excluded.error
            """, (document.id, document.filename, document.tenant_id, document.status.value, document.created_at.isoformat(), document.page_count, document.chunk_count, document.error))

    def list_all(self) -> list[DocumentResponse]:
        with connect(self.database_path) as connection:
            rows = connection.execute("SELECT * FROM documents").fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, document_id: str) -> None:
        with connect(self.database_path) as connection:
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))

    @staticmethod
    def _from_row(row) -> DocumentResponse:
        return DocumentResponse(
            id=row["id"], filename=row["filename"], tenant_id=row["tenant_id"],
            status=DocumentStatus(row["status"]), created_at=datetime.fromisoformat(row["created_at"]),
            page_count=row["page_count"], chunk_count=row["chunk_count"], error=row["error"],
        )
