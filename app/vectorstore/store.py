"""
In-memory vector store.
Stores chunk embeddings as lists and performs cosine similarity search.
Pure Python implementation (no numpy dependency).
"""
from __future__ import annotations
import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors (pure Python)."""
    if len(a) != len(b):
        raise ValueError("Vectors must have same dimension")
    
    # Dot product
    dot = sum(x * y for x, y in zip(a, b))
    
    # Norms
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """
    Simple in-memory vector store.

    Each entry:
        {
            "chunk_id": str,
            "doc_title": str,
            "source_doc_index": int,
            "text": str,
            "embedding": list[float],
        }
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add(self, chunk: dict, embedding: list[float]) -> None:
        """Add a single chunk with its embedding."""
        entry = {**chunk, "embedding": embedding}
        self._entries.append(entry)

    def add_many(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        """Bulk-add chunks with corresponding embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for chunk, emb in zip(chunks, embeddings):
            self.add(chunk, emb)
        logger.info("VectorStore: indexed %d chunks (total=%d)", len(chunks), len(self._entries))

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        threshold: float = 0.35,
    ) -> list[dict]:
        """
        Return the top-k most similar chunks whose similarity >= threshold.

        Each result dict contains all chunk fields plus a 'score' key.
        """
        if not self._entries:
            logger.warning("VectorStore is empty – no chunks indexed yet")
            return []

        scored: list[tuple[float, dict]] = []
        for entry in self._entries:
            score = _cosine_similarity(query_embedding, entry["embedding"])
            scored.append((score, entry))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        # Log top-5 scores for debugging
        for sc, ch in scored[:5]:
            logger.debug("  chunk='%s' score=%.4f", ch["chunk_id"], sc)

        # Filter by threshold and take top_k
        results = []
        for score, entry in scored[:top_k]:
            if score < threshold:
                logger.info(
                    "Chunk '%s' score %.4f below threshold %.2f – skipping",
                    entry["chunk_id"],
                    score,
                    threshold,
                )
                continue
            result = {k: v for k, v in entry.items() if k != "embedding"}
            result["score"] = round(score, 4)
            results.append(result)

        logger.info(
            "Search returned %d/%d chunks above threshold %.2f",
            len(results),
            top_k,
            threshold,
        )
        return results

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
