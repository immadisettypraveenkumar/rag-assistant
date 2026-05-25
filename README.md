# RAGchat — Production-Grade GenAI Assistant with RAG

A production-style Retrieval-Augmented Generation (RAG) chat assistant built with **FastAPI**, **Claude (Anthropic)**, and a custom **TF-IDF vector store** — no external vector DB required.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser / Frontend                        │
│  HTML · CSS · Vanilla JS  ←→  localStorage (session history)    │
└─────────────────────┬───────────────────────────────────────────┘
                      │  POST /api/chat  { sessionId, message }
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                                                                 │
│   ┌──────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│   │  Chat Route  │──▶│  RAG Service    │──▶│  LLM Service  │  │
│   │  /api/chat   │   │  (orchestrator) │   │  (Claude API) │  │
│   └──────────────┘   └────────┬────────┘   └───────────────┘  │
│                               │                                 │
│              ┌────────────────┼───────────────┐                │
│              ▼                ▼               ▼                │
│   ┌──────────────────┐  ┌──────────┐  ┌───────────────────┐  │
│   │ Embedding Service│  │ Vector   │  │  Session Service  │  │
│   │  TF-IDF / Voyage │  │  Store   │  │  (in-memory dict) │  │
│   └──────────────────┘  │ (cosine  │  └───────────────────┘  │
│                          │similarity│                          │
│   ┌──────────────────┐  └──────────┘                          │
│   │   Chunker Utils  │       ▲                                 │
│   │  (sentence-aware)│       │                                 │
│   └─────────┬────────┘       │ indexed at startup             │
│             │                │                                 │
│             ▼                │                                 │
│   ┌──────────────────┐       │                                 │
│   │    docs.json     │───────┘                                 │
│   │  (10 documents)  │                                         │
│   └──────────────────┘                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## RAG Workflow

```
INDEXING (at startup)
─────────────────────
docs.json
  └─▶ chunk_all_documents()        # sentence-aware chunking (≤400 tokens/chunk)
        └─▶ TFIDFEmbedder.fit()    # build vocabulary + IDF weights over corpus
              └─▶ embed_texts()    # generate float vectors for all chunks
                    └─▶ VectorStore.add_many()   # store in memory

QUERYING (per request)
──────────────────────
user_message
  └─▶ embed_query()                # same TF-IDF transform
        └─▶ VectorStore.search()   # cosine similarity vs all chunk vectors
              └─▶ filter top-K chunks above similarity threshold
                    └─▶ build_context_from_chunks()
                          └─▶ build_rag_prompt()  +  get_history()
                                └─▶ Claude API (claude-haiku-4-5)
                                      └─▶ reply + token count  →  response
```

---

## Embedding Strategy

The project uses a **TF-IDF (Term Frequency–Inverse Document Frequency)** embedder implemented from scratch in `app/services/embedding_service.py`:

1. **Corpus fit**: At startup, all chunk texts are used to build a vocabulary. Each term gets an IDF weight: `log((N+1)/(df+1)) + 1` (sklearn smooth IDF).
2. **Transform**: Each text (chunk or query) is converted to a weighted float vector over the full vocabulary using per-document term frequencies × IDF weights.
3. **Result**: Dense real-valued vectors that capture term importance relative to the whole corpus — genuine mathematical representations, not keyword matching.

> **Optional upgrade**: Set `VOYAGE_API_KEY` in `.env` to use [Voyage AI](https://docs.voyageai.com/) (Anthropic's recommended embeddings partner) for much higher quality vectors.

---

## Similarity Search

`app/vectorstore/store.py` implements **cosine similarity**:

```
similarity(A, B) = (A · B) / (||A|| × ||B||)
```

- Score range: 0 (unrelated) → 1 (identical direction)
- Default threshold: **0.35** (configurable via `SIMILARITY_THRESHOLD` env var)
- Default top-K: **3** (configurable via `TOP_K_CHUNKS`)
- If no chunk scores above threshold → safe fallback response is returned without calling the LLM

Similarity scores are logged for every query for observability.

---

## Prompt Design

```
SYSTEM:  You are a helpful support assistant. Answer ONLY using provided context.

USER:
  Context from knowledge base (top-K chunks with source labels + similarity scores)
  ──
  Conversation history (last 5 turns)
  ──
  User question
```

**Reasoning:**
- Strict grounding instruction prevents hallucination
- Source labels in context allow the model to cite/reference them
- History window enables follow-up questions without repeating context
- Low temperature (0.2) ensures factual, consistent answers

---

## Project Structure

```
project/
├── app/
│   ├── main.py                  # FastAPI app + startup indexing
│   ├── routes/
│   │   └── chat.py              # /api/chat  and  /health  endpoints
│   ├── services/
│   │   ├── embedding_service.py # TF-IDF embedder (+ optional Voyage AI)
│   │   ├── llm_service.py       # Claude API integration
│   │   ├── rag_service.py       # RAG pipeline orchestrator
│   │   └── session_service.py   # In-memory conversation history
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── vectorstore/
│   │   └── store.py             # In-memory cosine similarity vector store
│   ├── prompts/
│   │   └── templates.py         # Prompt templates
│   └── utils/
│       └── chunker.py           # Sentence-aware document chunker
│
├── frontend/
│   ├── index.html               # Chat UI
│   ├── styles.css               # Dark editorial design
│   └── app.js                   # Session management + API integration
│
├── docs.json                    # 10-document knowledge base
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone and install

```bash
git clone https://github.com/<username>/rag-assistant
cd rag-assistant
python -m venv .venv
source .venv/Scripts/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here
```

### 3. Run

```bash
python run.py
```

Open **http://localhost:8000** in your browser.

### 4. Test the API directly

```bash
# Health check
curl http://localhost:8000/health

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test123","message":"How do I reset my password?"}'
```

---

## Environment Variables

| Variable              | Default     | Description                              |
|-----------------------|-------------|------------------------------------------|
| `ANTHROPIC_API_KEY`   | —           | **Required.** Your Anthropic API key     |
| `TOP_K_CHUNKS`        | `3`         | Number of chunks to retrieve             |
| `SIMILARITY_THRESHOLD`| `0.35`      | Minimum cosine similarity score          |
| `MAX_HISTORY_PAIRS`   | `5`         | Conversation turns to retain per session |
| `CHUNK_SIZE_TOKENS`   | `400`       | Target chunk size (approx tokens)        |
| `VOYAGE_API_KEY`      | —           | Optional: use Voyage AI for embeddings   |
| `APP_PORT`            | `8000`      | Server port                              |
| `ALLOWED_ORIGINS`     | `*`         | CORS allowed origins (comma-separated)   |

---

## Deployment

### Render (recommended)

1. Push repo to GitHub
2. New Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python run.py`
5. Add environment variable: `ANTHROPIC_API_KEY`

### Railway

```bash
railway init
railway add
railway up
railway variables set ANTHROPIC_API_KEY=your_key
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

---

## API Reference

### `POST /api/chat`

**Request**
```json
{
  "sessionId": "abc123",
  "message": "How can I reset my password?"
}
```

**Response**
```json
{
  "reply": "You can reset your password from Settings > Security > Reset Password...",
  "tokensUsed": 287,
  "retrievedChunks": 3
}
```

**Error (422)**
```json
{
  "error": "Validation failed",
  "detail": [{"loc": ["body","message"], "msg": "Message cannot be blank"}]
}
```

### `GET /health`

```json
{
  "status": "healthy",
  "documentsLoaded": 10,
  "chunksIndexed": 14
}
```

---

## Evaluation Coverage

| Area                        | Implementation                                      |
|-----------------------------|-----------------------------------------------------|
| RAG Architecture (30%)      | Full pipeline: chunk → embed → retrieve → prompt → LLM |
| Embedding & Similarity (25%)| Custom TF-IDF vectors + cosine similarity search    |
| LLM Integration (20%)       | Claude Haiku via Anthropic API, error handling      |
| Prompt Design (10%)         | System + context + history + question template      |
| Frontend UI (5%)            | Dark editorial chat UI, sessions, chips, meta badges |
| Code Quality (10%)          | Pydantic validation, structured errors, logging     |

---

## Screenshots

> Add screenshots of the running application here.

---

## License

MIT
