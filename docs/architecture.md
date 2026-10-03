# Architecture

The API layer calls `RagService`, which orchestrates ingestion or retrieval through provider contracts. Tenant filtering is enforced before the vector search. The checked-in memory providers make local development deterministic; use Qdrant, Redis, Postgres, Docling, BGE-M3, and a queue worker before production deployment.
