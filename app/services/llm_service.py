"""
LLM service: integrates with Anthropic's Claude API.
Handles API failures, timeouts, invalid keys, and rate limits gracefully.
"""
from __future__ import annotations
import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024
TEMPERATURE = 0.2
API_URL = "https://api.anthropic.com/v1/messages"
REQUEST_TIMEOUT = 60.0


class LLMError(Exception):
    """Raised when the LLM call fails in a non-recoverable way."""


async def generate_response(
    prompt: str,
    system: str = "You are a helpful assistant.",
) -> tuple[str, int]:
    """
    Call Claude and return (reply_text, tokens_used).
    Raises LLMError on unrecoverable failures.
    """
    if not ANTHROPIC_API_KEY:
        raise LLMError("ANTHROPIC_API_KEY is not set. Please configure it in .env.")

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(API_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        logger.error("LLM request timed out after %.0fs", REQUEST_TIMEOUT)
        raise LLMError("The AI service timed out. Please try again.")
    except httpx.RequestError as exc:
        logger.error("LLM network error: %s", exc)
        raise LLMError("Unable to reach the AI service. Check your network connection.")

    # Handle HTTP errors
    if resp.status_code == 401:
        raise LLMError("Invalid API key. Please check your ANTHROPIC_API_KEY.")
    if resp.status_code == 429:
        logger.warning("Rate limit hit on Claude API")
        raise LLMError("Rate limit exceeded. Please wait a moment and try again.")
    if resp.status_code >= 500:
        logger.error("Claude API server error: %s", resp.status_code)
        raise LLMError("The AI service is temporarily unavailable. Please try again later.")
    if resp.status_code != 200:
        logger.error("Unexpected Claude API response: %s %s", resp.status_code, resp.text[:200])
        raise LLMError(f"Unexpected error from AI service (HTTP {resp.status_code}).")

    data = resp.json()
    reply_text: str = data["content"][0]["text"]
    usage = data.get("usage", {})
    tokens_used: int = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

    logger.info(
        "Claude response: model=%s tokens_in=%d tokens_out=%d",
        CLAUDE_MODEL,
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
    )

    return reply_text, tokens_used
