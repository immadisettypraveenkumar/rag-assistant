# RAGchat Installation Guide

A production-grade GenAI assistant with Retrieval-Augmented Generation (RAG).

---

## 🪟 Windows Users (5 Minutes)

1. **Extract** `rag-assistant-windows.zip`
2. **Open PowerShell** in the extracted folder
3. **Run**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-windows.txt
   copy .env.example .env
   ```
4. **Edit `.env`** and add your Anthropic API key
5. **Start server**:
   ```bash
   uvicorn app.main:app --reload
   ```
6. **Open** http://localhost:8000

**See `QUICKSTART_WINDOWS.md` for detailed Windows setup**

---

## 🐧 macOS / Linux

```bash
# Clone or extract the repository
cd rag-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY=sk-ant-...

# Run
uvicorn app.main:app --reload
```

Open **http://localhost:8000**

---

## 📋 Prerequisites

- **Python 3.11 or higher**
- **Anthropic API Key** (free tier available at https://console.anthropic.com)
- **Modern web browser**

---

## 🔧 Configuration

### Environment Variables

Edit `.env`:

```
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional (defaults shown)
APP_PORT=8000
TOP_K_CHUNKS=3
SIMILARITY_THRESHOLD=0.35
MAX_HISTORY_PAIRS=5
CHUNK_SIZE_TOKENS=400

# For production
ALLOWED_ORIGINS=https://yourdomain.com

# Optional: Use Voyage AI embeddings instead of TF-IDF
VOYAGE_API_KEY=your_voyage_key
```

---

## ✅ Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","documentsLoaded":10,"chunksIndexed":10}
```

---

## 🧪 Test Chat

### Via Browser
1. Go to http://localhost:8000
2. Type: "How do I reset my password?"
3. Observe: RAG retrieval, response generation, metadata

### Via cURL

**Windows (PowerShell)**:
```powershell
$body = @{
    sessionId = "test123"
    message = "How do I reset my password?"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/chat" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

**macOS/Linux**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"test123","message":"How do I reset my password?"}'
```

---

## 🚀 Deployment

### Option 1: Render (Recommended)

1. Push repo to GitHub
2. Create new **Web Service** on render.com
3. Connect your GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `ANTHROPIC_API_KEY=sk-ant-...`
7. Deploy

### Option 2: Railway

```bash
npm install -g @railway/cli
railway login
cd rag-assistant
railway init
railway add
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway up
```

### Option 3: Heroku

```bash
heroku create your-app-name
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
git push heroku main
```

### Option 4: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t rag-assistant .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... rag-assistant
```

---

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Use different port
uvicorn app.main:app --port 8001
```

### "Module not found" on Windows
```bash
# Make sure venv is activated (you should see (.venv) in terminal)
.venv\Scripts\activate
```

### "Invalid API key"
- Check your ANTHROPIC_API_KEY in `.env`
- Get key from: https://console.anthropic.com/
- Make sure it starts with `sk-ant-`

### Slow startup (30 seconds)
- Normal! The app indexes 10 documents at startup
- This only happens on first start

### "subprocess-exited-with-error" (numpy on Windows)
- Use `requirements-windows.txt` instead
- This file removes numpy dependency (all RAG features work without it)

---

## 📁 Project Structure

```
rag-assistant/
├── app/
│   ├── main.py                 # FastAPI + startup
│   ├── routes/chat.py          # API endpoints
│   ├── services/
│   │   ├── embedding_service.py    # TF-IDF embedder
│   │   ├── rag_service.py          # RAG orchestration
│   │   ├── llm_service.py          # Claude API
│   │   └── session_service.py      # Session management
│   ├── vectorstore/store.py    # In-memory vector DB
│   ├── prompts/templates.py    # Prompt engineering
│   └── utils/chunker.py        # Document chunking
├── frontend/
│   ├── index.html              # Chat UI
│   ├── styles.css              # Dark design
│   └── app.js                  # Session & API logic
├── docs.json                   # 10 sample documents
├── requirements.txt            # Standard deps
├── requirements-windows.txt    # Windows-optimized (no numpy)
├── .env.example               # Configuration template
├── README.md                  # Full documentation
├── QUICKSTART_WINDOWS.md      # Windows quick start
└── WINDOWS_SETUP.md           # Windows troubleshooting
```

---

## 📚 Features

✅ **RAG Pipeline**
- Document chunking (sentence-aware)
- TF-IDF embeddings (pure Python, no external API)
- Cosine similarity search
- Top-K retrieval with threshold

✅ **LLM Integration**
- Claude Haiku (fast, efficient)
- Temperature control
- Error handling (timeouts, rate limits, auth)
- Token tracking

✅ **Frontend**
- Dark editorial UI
- Session management
- Real-time typing indicator
- Message metadata (chunks, tokens)
- Responsive design

✅ **Developer Experience**
- Pydantic validation
- Structured error responses
- Comprehensive logging
- Environment configuration

---

## 🎓 Architecture

```
User Query
    ↓
Embed Query (TF-IDF)
    ↓
Vector Similarity Search
    ↓
Retrieve Top-K Chunks
    ↓
Build RAG Prompt (with history)
    ↓
Call Claude API
    ↓
Store Conversation Turn
    ↓
Return Response (with metadata)
```

---

## 📖 API Documentation

### POST /api/chat

**Request**:
```json
{
  "sessionId": "unique_session_id",
  "message": "Your question here"
}
```

**Response**:
```json
{
  "reply": "Answer based on knowledge base...",
  "tokensUsed": 287,
  "retrievedChunks": 3
}
```

### GET /health

**Response**:
```json
{
  "status": "healthy",
  "documentsLoaded": 10,
  "chunksIndexed": 10
}
```

---

## 🤝 Contributing

This is a complete, production-ready implementation. To extend:

1. **Add more documents**: Edit `docs.json`
2. **Use better embeddings**: Set `VOYAGE_API_KEY` for Voyage AI
3. **Store conversations**: Add database integration in `session_service.py`
4. **Customize UI**: Modify `frontend/` files
5. **Deploy**: Follow deployment section above

---

## ⚖️ License

MIT

---

## 🆘 Support

- **Windows issues?** → See `QUICKSTART_WINDOWS.md`
- **API errors?** → Check `.env` configuration
- **Embeddings questions?** → See `README.md` → Embedding Strategy
- **Deployment help?** → See Deployment section above

---

**Ready to deploy?** Push to GitHub and connect to Render, Railway, or your favorite platform.
