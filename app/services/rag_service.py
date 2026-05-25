"""
RAG Orchestration Service.

Flow:
1. Embed user query
2. Search vector store for top-k similar chunks
3. If no chunks above threshold → return fallback
4. Build context + prompt
5. Call LLM
6. Store conversation turn
7. Return reply
"""
from __future__ import annotations
import os
import logging

from app.services.embedding_service import embed_query
import app.services.llm_service as _llm_mod
from app.services.llm_service import LLMError
from app.services.session_service import get_history, add_turn
from app.prompts.templates import (
    build_rag_prompt,
    build_context_from_chunks,
    FALLBACK_RESPONSE,
    SYSTEM_PROMPT,
)
from app.vectorstore.store import VectorStore

logger = logging.getLogger(__name__)

TOP_K: int = int(os.getenv("TOP_K_CHUNKS", "3"))
THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.15"))


async def answer_question(
    session_id: str,
    user_message: str,
    vector_store: VectorStore,
) -> dict:
    """
    Full RAG pipeline.  Returns:
        {
            "reply": str,
            "tokensUsed": int,
            "retrievedChunks": int,
        }
    """
    logger.info("RAG query | session=%s | message='%s'", session_id, user_message[:80])

    # 1. Embed query
    query_embedding = embed_query(user_message)

    # 2. Vector similarity search
    chunks = vector_store.search(query_embedding, top_k=TOP_K, threshold=THRESHOLD)
    num_chunks = len(chunks)
    logger.info("Retrieved %d chunk(s) above threshold %.2f", num_chunks, THRESHOLD)

    # 3. Fallback if nothing useful retrieved
    if not chunks:
        add_turn(session_id, user_message, FALLBACK_RESPONSE)
        return {
            "reply": FALLBACK_RESPONSE,
            "tokensUsed": 0,
            "retrievedChunks": 0,
        }

    # 4. Build context and prompt
    context = build_context_from_chunks(chunks)
    history = get_history(session_id)
    prompt = build_rag_prompt(context=context, history=history, question=user_message)

    logger.debug("Prompt length: %d chars", len(prompt))

    # 5. Call LLM
    try:
        reply, tokens_used = await _llm_mod.generate_response(prompt, system=SYSTEM_PROMPT)
    except LLMError as exc:
        error_reply = f"Sorry, I encountered an error: {exc}"
        add_turn(session_id, user_message, error_reply)
        return {
            "reply": error_reply,
            "tokensUsed": 0,
            "retrievedChunks": num_chunks,
        }

    # 6. Persist conversation turn
    add_turn(session_id, user_message, reply)

    return {
        "reply": reply,
        "tokensUsed": tokens_used,
        "retrievedChunks": num_chunks,
    }