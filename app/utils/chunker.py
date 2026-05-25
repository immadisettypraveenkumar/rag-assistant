"""
Document chunking utility.
Splits documents into chunks of roughly CHUNK_SIZE tokens,
respecting sentence boundaries where possible.
"""
from __future__ import annotations
import re
import os
import logging

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS: int = int(os.getenv("CHUNK_SIZE_TOKENS", "400"))
# Rough approximation: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using simple punctuation rules."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def chunk_document(title: str, content: str, doc_index: int) -> list[dict]:
    """
    Chunk a single document into smaller pieces.

    Returns a list of chunk dicts:
        {
            "chunk_id": str,
            "doc_title": str,
            "source_doc_index": int,
            "text": str,
        }
    """
    max_chars = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN
    if not content or not content.strip():
        logger.debug("Skipping empty document '%s'", title)
        return []
    sentences = _split_sentences(content)

    chunks: list[dict] = []
    current: list[str] = []
    current_len = 0
    chunk_num = 0

    for sentence in sentences:
        slen = len(sentence)
        # If adding this sentence exceeds the limit AND we already have content, flush
        if current_len + slen > max_chars and current:
            chunk_text = " ".join(current)
            chunks.append(
                {
                    "chunk_id": f"doc{doc_index}_chunk{chunk_num}",
                    "doc_title": title,
                    "source_doc_index": doc_index,
                    "text": chunk_text,
                }
            )
            chunk_num += 1
            current = []
            current_len = 0

        current.append(sentence)
        current_len += slen + 1  # +1 for space

    # flush remainder
    if current:
        chunk_text = " ".join(current)
        chunks.append(
            {
                "chunk_id": f"doc{doc_index}_chunk{chunk_num}",
                "doc_title": title,
                "source_doc_index": doc_index,
                "text": chunk_text,
            }
        )

    logger.debug("Chunked doc '%s' into %d chunk(s)", title, len(chunks))
    return chunks


def chunk_all_documents(documents: list[dict]) -> list[dict]:
    """Chunk all documents and return a flat list of chunk dicts."""
    all_chunks: list[dict] = []
    for idx, doc in enumerate(documents):
        title = doc.get("title", f"Document {idx}")
        content = doc.get("content", "")
        all_chunks.extend(chunk_document(title, content, idx))
    logger.info("Total chunks created: %d from %d documents", len(all_chunks), len(documents))
    return all_chunks
