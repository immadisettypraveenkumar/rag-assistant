"""
Session service: stores conversation history per sessionId.
Keeps only the last MAX_HISTORY_PAIRS message pairs in memory.
"""
from __future__ import annotations
import os
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

MAX_HISTORY_PAIRS: int = int(os.getenv("MAX_HISTORY_PAIRS", "5"))

# { sessionId: [ {"role": "user"|"assistant", "content": str}, ... ] }
_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[dict]:
    """Return the message list for a session (most recent MAX_HISTORY_PAIRS pairs)."""
    history = _sessions[session_id]
    # Each pair = 1 user + 1 assistant message (2 entries)
    max_messages = MAX_HISTORY_PAIRS * 2
    return history[-max_messages:]


def add_turn(session_id: str, user_message: str, assistant_reply: str) -> None:
    """Append a user/assistant turn to the session history."""
    _sessions[session_id].append({"role": "user", "content": user_message})
    _sessions[session_id].append({"role": "assistant", "content": assistant_reply})
    # Trim to avoid unbounded growth
    max_messages = MAX_HISTORY_PAIRS * 2
    if len(_sessions[session_id]) > max_messages:
        _sessions[session_id] = _sessions[session_id][-max_messages:]
    logger.debug("Session '%s': %d messages stored", session_id, len(_sessions[session_id]))


def clear_session(session_id: str) -> None:
    """Clear history for a specific session."""
    _sessions.pop(session_id, None)
    logger.info("Session '%s' cleared", session_id)


def session_count() -> int:
    return len(_sessions)
