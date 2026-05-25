"""
Main Flask application.
On startup: loads docs.json → chunks → builds TF-IDF embedder → indexes into VectorStore.
Run with: python run.py
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

from app.utils.chunker import chunk_all_documents
from app.services.embedding_service import build_embedder, embed_texts
from app.vectorstore.store import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="../frontend", static_url_path="/static")
CORS(app)

# ── Global state ───────────────────────────────────────────────────────────
vector_store: VectorStore | None = None
docs_loaded: int = 0


def index_documents() -> None:
    """Load docs.json, chunk, embed, and index into vector store."""
    global vector_store, docs_loaded

    docs_path = Path(__file__).parent.parent / "docs.json"
    logger.info("Loading documents from %s", docs_path)

    with open(docs_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    docs_loaded = len(documents)
    chunks = chunk_all_documents(documents)
    corpus_texts = [c["text"] for c in chunks]

    build_embedder(corpus_texts)
    embeddings = embed_texts(corpus_texts)

    vector_store = VectorStore()
    vector_store.add_many(chunks, embeddings)
    logger.info("Indexed %d chunks from %d documents", vector_store.count, docs_loaded)


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def serve_frontend():
    from flask import send_from_directory
    frontend_path = Path(__file__).parent.parent / "frontend"
    return send_from_directory(str(frontend_path), "index.html")


@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "documentsLoaded": docs_loaded,
        "chunksIndexed": vector_store.count if vector_store else 0,
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    import asyncio
    from app.services.rag_service import answer_question

    # Parse and validate JSON body
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    body = request.get_json(silent=True) or {}
    session_id = str(body.get("sessionId", "")).strip()
    message = str(body.get("message", "")).strip()

    if not session_id:
        return jsonify({"error": "sessionId is required"}), 422
    if not message:
        return jsonify({"error": "message is required"}), 422

    if vector_store is None or vector_store.count == 0:
        return jsonify({"error": "Knowledge base not ready. Try again in a moment."}), 503

    result = asyncio.run(answer_question(
        session_id=session_id,
        user_message=message,
        vector_store=vector_store,
    ))

    return jsonify({
        "reply": result["reply"],
        "tokensUsed": result["tokensUsed"],
        "retrievedChunks": result["retrievedChunks"],
    })


# ── Startup ────────────────────────────────────────────────────────────────
index_documents()