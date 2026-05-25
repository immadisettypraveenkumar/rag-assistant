"""
API routes: POST /api/chat and GET /health
Returns plain dicts to avoid pydantic schema-generation issues across versions.
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import ChatRequest
from app.services.rag_service import answer_question

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    vs = getattr(request.app.state, "vector_store", None)
    docs_loaded = getattr(request.app.state, "docs_loaded", 0)
    chunks_indexed = vs.count if vs is not None else 0
    return {
        "status": "healthy",
        "documentsLoaded": docs_loaded,
        "chunksIndexed": chunks_indexed,
    }


@router.post("/api/chat")
async def chat(request: Request, body: ChatRequest):
    """
    Main chat endpoint. Validates input, runs the RAG pipeline,
    and returns a grounded response.
    """
    vs = getattr(request.app.state, "vector_store", None)

    if vs is None or vs.count == 0:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base is not yet indexed. Please try again in a moment.",
        )

    result = await answer_question(
        session_id=body.sessionId,
        user_message=body.message,
        vector_store=vs,
    )

    return {
        "reply": result["reply"],
        "tokensUsed": result["tokensUsed"],
        "retrievedChunks": result["retrievedChunks"],
    }