# Automique RAG

Provider-swappable PDF RAG service with three-layer PDF parsing (MinerU → Docling → pypdf), fast-path detection, GPU acceleration, parallel processing, and async pipeline overlap. The codebase follows a layered `src/` layout: HTTP routers, schemas, core RAG logic, providers, workers, evaluation, and documentation are isolated by responsibility.

## Key Features

- **Three-layer PDF parsing fallback**:
  1. **MinerU (primary)**: Best layout/table/formula extraction
  2. **Docling (first fallback)**: Layout-aware Markdown without OCR
  3. **pypdf (final fallback)**: Basic text extraction
- **Fast-path detection**: Quick pypdf check to skip ML layers for text-rich PDFs (~0.5s)
- **Performance optimizations**:
  - GPU acceleration for MinerU/Docling (`MINERU_DEVICE=cuda`, `DOCLING_DEVICE=cuda`)
  - Parallel page processing (configurable workers)
  - Async batch embedding/upsert (32-chunk batches)
  - Feature toggles to disable heavy features (formulas/tables)
- **Comprehensive guardrails (Laya-powered)**:
  - OCR quality gate (Scenario A: gibberish PDF → failed)
  - Relevance gate (Scenario B: out-of-scope query → abstained)
  - Faithfulness gate (Scenario C: hallucination → abstained)
  - Citation verification
  - Prompt injection protection
- **Tenant isolation** at the store level (SQLite/Memory/Qdrant)
- **Semantic caching** (in-memory, cosine threshold 0.95)
- **Hybrid retrieval** (dense cosine + lexical term matching → RRF fusion)
- **Parent-child chunking** for context preservation
- **OpenAPI docs** at `/docs`

## Performance (11-page Attention paper)

| Scenario | Time |
|----------|------|
| Text PDF (fast-path) | ~0.5-1s |
| Complex PDF (CPU, parallel) | ~16s |
| Complex PDF (GPU + parallel) | ~2-4s |
| Scanned PDF (GPU + parallel) | ~3-5s |

*Times include parsing, chunking, embedding (Ollama nomic-embed-text), and indexing.*

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

`POST /api/v1/chat` takes a tenant-scoped question, optional `document_ids`, and `stream: true` for SSE. Configure `LLM_BASE_URL` and `LLM_MODEL` to use any OpenAI-compatible gateway such as LiteLLM, Ollama, vLLM, or TGI.

## Runtime model

The local default uses a deterministic embedding provider (`HashEmbeddingProvider`) and memory-backed hybrid index, making development and tests work without services. `docker-compose.yml` provisions the production dependencies, while the provider and worker modules mark the implementation points for the persistent setup.

## Next adapters

The protocol boundaries in `src/providers/` are the intended extension points:

- Replace `HashEmbeddingProvider` with BGE-M3 through sentence-transformers or TEI.
- Replace `MemoryHybridStore` with a Qdrant/OpenSearch implementation and persist document metadata in Postgres.
- Add authentication, virus scanning, durable feedback/audit storage, and Langfuse instrumentation before handling sensitive production documents.

The current service enforces tenant filtering in the retrieval path, performs dense and lexical rank fusion, expands child chunks to parent context, gates weak matches, and returns source citations.

## Guardrail Scenarios

See `test_scenarios.py` for end-to-end tests of:

- **Scenario A**: OCR quality gate (gibberish PDF → failed)
- **Scenario B**: Relevance gate (out-of-scope query → abstained)
- **Scenario C**: Faithfulness gate (hallucination → abstained)

## Configuration

Key settings in `.env` (see `.env.example`):

```
# Parsing optimization
PARSER_FAST_PATH=true
PARSER_FAST_PATH_MIN_CHARS=50
PARSER_FAST_PATH_SAMPLE_PAGES=3
MINERU_FORMULA_ENABLE=true
MINERU_TABLE_ENABLE=true
DOCLING_IMAGES_SCALE=1.0
PARSER_PARALLEL_WORKERS=4

# Device acceleration (set to "cuda" for GPU)
MINERU_DEVICE=
DOCLING_DEVICE=

# Laya guardrails
LAYA_ENABLED=false
LAYA_MODEL=
LAYA_DEVICE=
LAYA_MAX_CONTEXT_CHARS=2000
LAYA_RELEVANCE_THRESHOLD=0.5
LAYA_FAITHFULNESS_THRESHOLD=0.5
LAYA_CITATION_THRESHOLD=0.5
LAYA_OCR_QUALITY_THRESHOLD=0.4
LAYA_RERANK_TOP_N=10

# Embedding
EMBEDDING_PROVIDER=hash   # or ollama
EMBEDDING_DIMENSION=256
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# LLM
LLM_BASE_URL=
LLM_MODEL=
LLM_API_KEY=
LLM_MAX_TOKENS=350
LLM_TIMEOUT_SECONDS=120
```