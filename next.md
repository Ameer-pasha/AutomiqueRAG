# Automique RAG: completed work and next handoff

## What I completed

I built and verified a local, persistent PDF question-answering system. It is a standard hybrid RAG pipeline, not Agentic RAG or Graph RAG.

```text
PDF upload
  -> validation
  -> tenant-wise file storage
  -> page text extraction
  -> overlapping chunks with page metadata
  -> Ollama embeddings
  -> SQLite persistent vector storage
  -> semantic + lexical retrieval and RRF fusion
  -> relevance gate
  -> Ollama answer generation
  -> citations with document and page numbers
```

### Application and API

- Created the FastAPI application in `src/main.py`.
- Added API endpoints:
  - `POST /api/v1/documents`: upload a PDF.
  - `GET /api/v1/documents/{id}`: check ingestion status.
  - `DELETE /api/v1/documents/{id}`: delete document chunks and original PDF.
  - `POST /api/v1/chat`: ask a question about uploaded documents.
  - `POST /api/v1/feedback`: accept user feedback.
  - `GET /api/v1/health`: inspect active providers.
  - `GET /api/v1/admin/stats`: see document and feedback counts.
  - `POST /api/v1/admin/reindex/{id}`: rebuild embeddings when the embedding model changes.
- Added `X-Tenant-ID` filtering. A tenant can retrieve only its own chunks.

### Ingestion and storage

- Added PDF extension, signature, and max-size validation.
- Uploaded PDFs are stored at `data/files/<tenant-id>/<document-id>.pdf`.
- `pypdf` extracts text from every page of a digital/selectable-text PDF.
- Parent-child style overlapping chunks are created with filename, page, section, document ID, and tenant metadata.
- Added SQLite persistence in `data/rag.db`:
  - `documents` table stores upload status and document metadata.
  - `chunks` table stores chunk text, metadata, and vectors.
  - Documents and retrieval data survive FastAPI reloads/restarts.

### Retrieval and answer generation

- Added Ollama embedding provider: `nomic-embed-text:latest`.
- Added Ollama OpenAI-compatible LLM gateway: `llama3.2:latest`.
- Added dense retrieval, local lexical ranking, Reciprocal Rank Fusion (RRF), parent-context building, and relevance threshold gating.
- Added short semantic cache in memory for repeated questions.
- Added grounded prompt rules: answer from supplied document context only, treat PDF text as untrusted data, and say information is unavailable when unsupported.
- Added citations containing document ID, filename, page number, and chunk ID.
- Limited local generation to three context chunks, 350 output tokens, and 120 seconds so Ollama works reliably on local hardware.

### Project quality and operations

- Created `learn.md` with complete run, upload, storage, delete, and architecture instructions.
- Created Docker, Docker Compose, Makefile, evaluation, scripts, test, and docs scaffolding.
- Added unit and integration tests. Current result: `3 passed`.
- Verified a 21-page RAG paper indexed into 60 chunks and generated a cited five-bullet summary through Ollama.

## Current run commands

Open one PowerShell terminal for Ollama only if it is not already running:

```powershell
ollama serve
```

Open another PowerShell terminal for the API:

```powershell
cd F:\Automique-rag
.\.venv\Scripts\Activate.ps1
py -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8001
```

Use the API here:

```text
http://127.0.0.1:8001/docs
```

## What my friend should build next

### Goal: scanned PDF support through Docling and OCR

The current system works for digital PDFs where text can be selected and copied. It does not yet reliably support scanned/image-only PDFs, handwritten pages, or difficult tables. My friend should add this capability without changing the working retrieval, SQLite, or Ollama paths.

### Files my friend should modify

```text
pyproject.toml
src/core/ingestion/parser.py
src/core/ingestion/scanned.py
src/core/ingestion/pipeline.py
tests/fixtures/
tests/integration/
learn.md
```

### Files my friend should not modify

```text
src/services.py
src/dependencies.py
src/api/chat.py
src/providers/embeddings/ollama.py
src/providers/llm/
src/providers/vectorstore/sqlite_store.py
src/db/
```

### Required implementation

1. Add Docling as the primary PDF parser dependency.
2. Parse each PDF into clean text/Markdown while preserving original page numbers.
3. Keep `pypdf` as a fallback for simple digital PDFs if Docling fails or is unavailable.
4. Check every page with `needs_ocr()`:
   - Good text page: use normal parser output.
   - Little/no text: run an OCR adapter.
5. Choose one OCR engine first, preferably Docling built-in OCR or RapidOCR.
6. Return the same output shape expected by `chunk_pages()`:
   - page text
   - page number
   - section/heading when available
   - table text kept together where possible
7. Keep status transitions working:

```text
queued -> parsing -> chunking -> indexing -> indexed
```

8. If OCR fails, document status must become `failed` with a useful `error` message.
9. Add tests with:
   - one normal digital PDF
   - one scanned/image-only PDF
   - one invalid/non-PDF input
10. Update `learn.md` with scanned-PDF requirements, performance expectations, and any extra setup steps.

### Definition of done for my friend

```text
Upload a digital PDF -> indexed -> chat answer with citations.
Upload a scanned PDF -> indexed -> chat answer with citations.
Page citations match the original PDF page.
Existing digital-PDF behavior still passes tests.
No changes break SQLite persistence, Ollama embeddings, or chat generation.
```

## Work after OCR

After scanned PDFs work, the next priority is retrieval quality:

1. Build a true BM25 index over all chunks, not just lexical reordering of dense results.
2. Add a cross-encoder reranker for the top candidates.
3. Add citation/faithfulness verification.
4. Build a golden question-answer set and measure Recall@k, MRR, faithfulness, and answer relevancy.
5. Only then move from local SQLite to Qdrant, Redis, Postgres, and a durable worker for production scale.
