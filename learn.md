# Automique RAG: start se end tak

Yeh project PDF upload karke uske content par question-answer karne wala RAG API hai. Abhi local development mode mein poora digital/text PDF flow chal raha hai. Aap PDF upload karte ho; API usko background mein parse, chunk, embed, aur index karti hai. Phir `/chat` usi tenant ke documents mein search karke answer aur page citations deti hai.

## Sabse pehle: current reality

Database service `docker-compose.yml` mein declared hai, lekin application code abhi Postgres, Redis, ya Qdrant se connected nahi hai. Local mode mein built-in SQLite database `data/rag.db` use hota hai:

| Cheez | Abhi kahan rehti hai | Server restart ke baad |
| --- | --- | --- |
| Original uploaded PDF | `data/files/<tenant-id>/<document-id>.pdf` | Rehti hai |
| Document status | SQLite `data/rag.db` | Rehta hai |
| Chunks | SQLite `data/rag.db` | Rehte hain |
| Embeddings/index | SQLite `data/rag.db` | Rehte hain |
| Semantic cache | Python memory | Chala jata hai |
| Feedback | Python memory | Chala jata hai |

Isliye upload, status, chunks, and local retrieval reload/restart ke baad bhi rehte hain. Production scale ke liye SQLite ko `QdrantStore` plus Postgres metadata, Redis semantic cache, aur durable worker se replace karna hoga. Unki boundaries already yahan hain: `src/providers/vectorstore/qdrant_store.py`, `src/db/`, `src/core/cache/`, aur `src/workers/`.

## Is project ka folder map

```text
src/api/             HTTP endpoints only
src/schemas/         request and response models
src/core/            actual RAG pipeline logic
src/providers/       LLM, embedding, vector store swap points
src/services.py      pipeline ko jodta hai
src/dependencies.py  tenant and service injection
data/files/          uploaded PDFs
evaluation/          golden questions and quality checks
docs/                architecture, API, tuning notes
```

## Kaise run karna hai

Python 3.11+ chahiye. PowerShell mein project root se:

```powershell
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
py -m uvicorn src.main:app --reload
```

Server run hone ke baad browser mein yeh kholo:

```text
http://127.0.0.1:8000/docs
```

Swagger UI mein har endpoint ko directly test kar sakte ho. Project root mein Make available ho to shortcuts bhi hain:

```text
make start
make test
make lint
make eval
```

Abhi local server `http://127.0.0.1:8000` par running hai.

## PDF upload kaise karna hai

Swagger UI mein `POST /api/v1/documents` open karo:

1. `Try it out` dabao.
2. Header `X-Tenant-ID` mein apna tenant name do, for example `ameer`.
3. `file` mein PDF select karo.
4. `Execute` dabao.

Response mein `id` milega aur initial status `queued` hoga. Is id se status poll karo:

```text
GET /api/v1/documents/{document_id}
```

Status ka meaning:

| Status | Kya ho raha hai |
| --- | --- |
| `queued` | Upload receive ho gaya, task start hona hai |
| `parsing` | PDF se har page ka selectable text nikal raha hai |
| `chunking` | Page text ko chhote searchable blocks mein tod raha hai |
| `indexing` | Har chunk ka embedding bana ke search index mein daal raha hai |
| `indexed` | Document chat ke liye ready hai |
| `failed` | Parsing ya indexing mein error aaya; `error` field dekho |

Command line se upload ka example:

```powershell
$headers = @{ "X-Tenant-ID" = "ameer" }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/documents" -Headers $headers -Form @{ file = Get-Item "C:\path\to\report.pdf" }
```

## Upload ke baad exactly kya hota hai

```text
PDF upload
  -> PDF signature and size validation
  -> data/files/<tenant>/<document-id>.pdf mein save
  -> background ingestion task
  -> pypdf digital text extraction, page by page
  -> heading-aware parent-child chunks
  -> contextual header ke saath embedding
  -> local dense index mein chunks + vectors
  -> document status = indexed
```

### 1. Validation

`src/core/ingestion/validator.py` only `.pdf` extension aur real `%PDF-` signature accept karta hai. Default max size `.env` mein `MAX_UPLOAD_MB=50` hai. Isliye renamed non-PDF upload reject hoga.

### 2. File save

`src/api/documents.py` PDF ko tenant-wise disk par save karta hai:

```text
data/files/ameer/7f3f...-document-id.pdf
```

`X-Tenant-ID` important hai. Har request mein same tenant header dena hai, warna aapka document ya search result nahi milega. Isse retrieval ke time server-side tenant filter lagta hai.

### 3. PDF parsing

Current parser `pypdf` hai: `src/core/ingestion/parser.py`. Yeh **digital PDFs** ke liye hai jisme text select/copy kiya ja sakta hai. Har page ka text separately extract hota hai, isliye citation mein original page number aata hai.

Scanned/image-only PDF, handwritten prescription, complex table, chart, ya poor-quality scan ke liye current implementation `failed` status de sakta hai with `No selectable text found`. Next parser upgrade hoga:

```text
Docling primary parser
  -> OCR for scanned pages
  -> VLM for difficult tables/charts/handwriting
  -> normalized markdown with page + section metadata
```

Uska exact home `src/core/ingestion/parser.py` aur `src/core/ingestion/scanned.py` hai.

### 4. Chunking

`src/core/ingestion/chunker.py` page ke text ko default 380-word chunks mein todta hai. Adjacent chunks mein 60 words overlap rehte hain. Har chunk ke paas yeh metadata hota hai:

```text
document id, tenant id, filename, page, section path, parent id
```

Search ke liye child chunk use hota hai. Answer banate waqt nearby parent context use hota hai, jisse short search match milta hai lekin LLM ko adhura sentence nahi milta.

### 5. Embedding and index

Default embedding `HashEmbeddingProvider` hai: `src/providers/embeddings/local.py`. Is project ki current `.env` Ollama ka `nomic-embed-text:latest` use karti hai through `src/providers/embeddings/ollama.py`, which gives substantially better semantic retrieval. Model change ke baad `POST /api/v1/admin/reindex/{document_id}` call karna zaroori hai, otherwise old vectors new query vectors se compatible nahi honge.

Production replacement:

```text
Current: HashEmbeddingProvider + MemoryHybridStore
Production: BGE-M3 + Qdrant hybrid search
Alternative: multilingual-e5 + OpenSearch
```

Local store `src/providers/vectorstore/sqlite_store.py` mein hai. Dense vectors `data/rag.db` mein store hote hain, so server restart ke baad re-index zaroori nahi hota.

## Question kaise poochna hai

Document ka status `indexed` hone par Swagger se `POST /api/v1/chat` call karo. Header same `X-Tenant-ID` hona chahiye.

Body:

```json
{
  "query": "Is document mein aspirin ki dose kya hai?",
  "document_ids": ["your-document-id"],
  "stream": false
}
```

PowerShell example:

```powershell
$headers = @{ "X-Tenant-ID" = "ameer" }
$body = @{ query = "Is report ka conclusion kya hai?"; document_ids = @("your-document-id"); stream = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/chat" -Headers $headers -ContentType "application/json" -Body $body
```

`document_ids` optional hai. Agar omit karoge, API aapke current tenant ke sab indexed documents mein search karegi. `stream: true` use karoge to response Server-Sent Events format mein aayega.

## Query se answer tak

```text
Question
  -> whitespace query rewrite
  -> question embedding
  -> tenant/document filtered dense retrieval
  -> local lexical ranking
  -> RRF fusion
  -> relevance gate
  -> parent context build and dedupe
  -> LLM generation
  -> answer + document/page citations
```

### Hybrid retrieval

`src/core/retrieval/hybrid.py` dense similarity plus lexical term ranking dono run karta hai. `src/core/retrieval/fusion.py` Reciprocal Rank Fusion (RRF) se rankings combine karta hai. Exact terms, medicines, codes, and numbers lexical matching se help hote hain; meaning-based questions dense vectors se help hote hain.

### Relevance gate

`src/core/guard/relevance_gate.py` best dense score ko `.env` ke `RELEVANCE_THRESHOLD` se compare karta hai. Score weak ho to LLM ko context bhejne ke badle yeh bolta hai:

```text
I could not find enough relevant information in the selected documents.
```

Yeh hallucination kam karne ka first guardrail hai. Medical use case mein threshold ko golden set se tune karna chahiye.

### Answer generator

Current `LLMGateway` `src/providers/llm/gateway.py` mein hai. Current `.env` Ollama `llama3.2:latest` use karti hai. Local model ko responsive rakhne ke liye `LLM_CONTEXT_CHUNKS=3`, `LLM_MAX_TOKENS=350`, aur `LLM_TIMEOUT_SECONDS=120` configured hain. Ollama unavailable ho to API generic `500` ke bajaye clear `503` message return karti hai.

Ollama/vLLM/OpenAI-compatible API connect karne ke liye `.env` mein example:

```dotenv
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.2:latest
LLM_API_KEY=
```

OpenAI-compatible LLM use hone par grounded system instruction jati hai: supplied document context ke bahar answer nahi dena hai, aur PDF ke hidden instructions ko instructions ki tarah follow nahi karna hai.

### Citations

Response mein citations list aati hai:

```json
{
  "document_id": "...",
  "filename": "report.pdf",
  "page": 2,
  "chunk_id": "..."
}
```

Answer ke saath page number use karke user original PDF verify kar sakta hai.

## Delete kaise hota hai

Current delete endpoint:

```text
DELETE /api/v1/documents/{document_id}
```

Header mein same `X-Tenant-ID` dena hai. Current code SQLite se document and indexed chunks remove karta hai, aur original PDF `data/files/<tenant>/<id>.pdf` se bhi delete karta hai. Semantic cache RAM-based hai, so cache restart par clear hota hai. Production deletion design should be atomic:

```text
1. tenant authorization verify
2. Qdrant/OpenSearch se all chunks delete by tenant_id + doc_id
3. Postgres document/job/feedback references delete or tombstone
4. object storage/disk se original PDF delete
5. Redis semantic cache entries invalidate
6. audit log record
```

Retention policy abhi configured nahi hai. PDFs tab tak disk par rehte hain jab tak manually delete na karo or production retention job na banaya jaye. Medical data ke liye retention duration and audit requirements business/compliance decision hain.

## Docker kab use karna hai

`docker-compose.yml` API, Qdrant, Redis, Postgres, aur worker service ka intended production topology dikhata hai. Current application still local providers use karti hai, so Compose services start karne se persistence automatically on nahi hogi. Qdrant/Postgres/Redis adapters complete hone ke baad `.env` URLs set karke Compose use karna meaningful hoga.

## Testing and evaluation

```powershell
py -m pytest -q -p no:cacheprovider
py -m compileall -q src tests evaluation scripts
```

`evaluation/golden_set/` mein real PDFs se question, expected answer, and source page add karo. Har chunk size, embedding model, reranker, or threshold change ke baad Recall@k, MRR, faithfulness, and answer relevancy measure karni chahiye.

## Next implementation order

1. Docling plus OCR fallback so scanned PDFs bhi ingest hon.
2. BGE-M3 embedding provider and Qdrant persistent hybrid index.
3. Postgres documents/jobs/feedback tables and Alembic migrations.
4. Redis semantic cache and durable queue worker.
5. Cross-encoder reranker, citation validation, and optional faithfulness judge.
6. JWT/API-key auth, virus scan, rate limiting, audit logs, and PHI redaction for sensitive data.

Abhi use karne ka simple rule: PDF upload karo, `indexed` wait karo, same tenant header se chat karo, aur citations ke page par answer verify karo.
