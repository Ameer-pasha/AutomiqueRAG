# Automique RAG

Provider-swappable PDF RAG service. The codebase follows a layered `src/` layout: HTTP routers, schemas, core RAG logic, providers, workers, evaluation, and documentation are isolated by responsibility.


## Run locally

```powershell
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
py -m uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API. Run tests with `pytest`.

Read [learn.md](learn.md) for the end-to-end upload, retrieval, storage, deletion, and deployment walkthrough.

## API

`POST /api/v1/documents` accepts a PDF and returns an asynchronous job record. Poll `GET /api/v1/documents/{id}` until its status is `indexed`.

`POST /api/v1/chat` takes a tenant-scoped question, optional `document_ids`, and `stream: true` for SSE. The local answer generator is extractive; configure `LLM_BASE_URL` and `LLM_MODEL` to use any OpenAI-compatible gateway such as LiteLLM, Ollama, vLLM, or TGI.

## Runtime model

The local default uses a deterministic embedding provider and memory-backed hybrid index, making development and tests work without services. `docker-compose.yml` provisions the production dependencies, while the provider and worker modules mark the implementation points for the persistent setup.

## Next adapters

The protocol boundaries in `src/providers/` are the intended extension points:

- Replace `HashEmbeddingProvider` with BGE-M3 through sentence-transformers or TEI.
- Replace `MemoryHybridStore` with a Qdrant/OpenSearch implementation and persist document metadata in Postgres.
- Add Docling with OCR/VLM fallback in `src/core/ingestion/` for scanned or complex PDFs.
- Move `ingest_document` to a Redis-backed worker before running multiple API replicas.
- Add authentication, virus scanning, durable feedback/audit storage, and Langfuse instrumentation before handling sensitive production documents.

The current service enforces tenant filtering in the retrieval path, performs dense and lexical rank fusion, expands child chunks to parent context, gates weak matches, and returns source citations.
