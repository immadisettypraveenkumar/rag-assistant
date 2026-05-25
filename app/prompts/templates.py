"""
Prompt templates for the RAG assistant.
"""

SYSTEM_PROMPT = """You are a knowledgeable and helpful support assistant.

Your job is to answer user questions ONLY using the provided context from the knowledge base.

Rules:
- Base your answer strictly on the provided context. Do not invent facts.
- If the context does not contain enough information, say so honestly.
- Be concise but thorough. Use bullet points or numbered lists when helpful.
- Maintain a friendly, professional tone.
- If a previous conversation is available, use it to understand follow-up questions.
"""

RAG_PROMPT_TEMPLATE = """You are a knowledgeable and helpful support assistant.

Answer the user's question using ONLY the context provided below. Do not use any outside knowledge.
If the context does not contain enough information to answer confidently, respond with:
"I could not find enough information in the knowledge base to answer this question."

---

CONTEXT FROM KNOWLEDGE BASE:
{context}

---

CONVERSATION HISTORY:
{history}

---

USER QUESTION:
{question}

---

Provide a clear, accurate, and helpful answer based solely on the context above."""


FALLBACK_RESPONSE = (
    "I could not find enough information in the knowledge base to answer this question. "
    "Please try rephrasing your question or contact support for further assistance."
)


def build_rag_prompt(context: str, history: list[dict], question: str) -> str:
    """Build the full RAG prompt string."""
    if history:
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in history
        )
    else:
        history_text = "No previous conversation."

    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        history=history_text,
        question=question,
    )


def build_context_from_chunks(chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context string."""
    if not chunks:
        return "No relevant context found."
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i}: {chunk['doc_title']} | similarity={chunk['score']:.2f}]\n{chunk['text']}"
        )
    return "\n\n".join(parts)
