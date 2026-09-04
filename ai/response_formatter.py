"""
ai/response_formatter.py
Post-processing / validation of assistant responses.

The LLM can occasionally return empty, malformed, or overly long answers, or
attempt to write something outside the ground rules. This module sanitises and
validates the response, and provides a user-friendly fallback message when the
model output can't be used.
"""

from __future__ import annotations

import re
from typing import Optional

# A guard list kept minimal and user-facing-safe (not an exhaustive profanity
# filter - it only catches the most common case-insensitive coarse tokens that
# would be inappropriate even in a professional analytics app).
_SCOPE_GUARD_TOKENS = [
    "api key",
    "api_key",
    "secret key",
    "GEMINI_API_KEY",
    "password:",
    "my password is",
]


def _is_empty(text: Optional[str]) -> bool:
    return text is None or not str(text).strip()


def clean_response(response: Optional[str]) -> Optional[str]:
    """Trim and lightly normalise a raw model response.

    Returns a cleaned string or None if there is nothing usable.
    """
    if _is_empty(response):
        return None
    text = str(response).strip()
    # Collapse an accidental trailing sequence of repeated delimiters.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def validate_response(response: Optional[str]) -> Optional[str]:
    """Validate a response for basic safety.

    Returns the cleaned response if acceptable, otherwise None.
    """
    cleaned = clean_response(response)
    if cleaned is None or len(cleaned) < 2:
        return None
    lowered = cleaned.lower()
    # If the model appears to have leaked a secret/credential, drop the answer.
    for token in _SCOPE_GUARD_TOKENS:
        if token in lowered:
            return None
    return cleaned


def fallback_message(error: str = "response") -> str:
    """A stable, user-friendly message when the model answer can't be shown."""
    return (
        "I couldn't produce a grounded answer just now "
        f"({error}). Please try again, or rephrase your question. "
        "If this keeps happening, check the LLM configuration."
    )


def format_conversation_turn(cleaned: str) -> str:
    """Final display formatting (currently just ensures the text is a string)."""
    return str(cleaned)


def extract_context_delta(response: Optional[str]) -> str:
    """Minimal length guard helper - not used to alter content, kept for tests.

    Returns a short hint of how many characters of context a response used, to
    keep the API contract explicit.
    """
    return f"{len(response) if response else 0} chars"
