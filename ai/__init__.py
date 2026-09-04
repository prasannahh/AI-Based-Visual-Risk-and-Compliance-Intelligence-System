"""
ai
==

Milestone 4 - Conversational AI & Interactive Dashboard service layer.

This package provides a clean, provider-agnostic Conversational AI layer for
the Digital Twin Decision Assistant. It builds a controlled, grounded context
from the user's real Digital Twin data (via the existing database.simulation
and ai_models services) and lets an LLM explain / personalise those
already-computed results without ever inventing data.

The LLM is intentionally NOT the source of truth: the deterministic project
engines (db., simulation.*, ai_models.*) are. The AI layer only narrates and
personalises what those engines produce.

AI Provider Architecture:
    PRIMARY:  Gemini API (google-genai)
    FALLBACK: Built-in rule-based deterministic assistant (no API key needed)

When Gemini is configured but unavailable (missing key, API error, timeout,
network failure, rate limit, empty response), the system automatically falls
back to the rule-based assistant without crashing.

Typical data flow::

    Streamlit UI
         |
    conversation_service.py
         |
    context_builder.py  ->  existing db / simulation / ai_models services
         |
    llm_client.py  (provider abstraction: gemini | rule-based)
         |
    response_formatter.py  (validation / safety formatting)
         |
    Streamlit Chat UI

Submodules
----------
config:
    Reads LLM provider + credentials from environment / secrets.
llm_client:
    LLMClient abstraction with Gemini and rule-based fallback clients.
prompt_templates:
    System prompt + AI grounding rules; kept separate from user messages.
context_builder:
    Builds the structured Digital Twin context sent to the LLM.
conversation_service:
    Orchestrates context building, LLM invocation, automatic fallback
    and response validation.
response_formatter:
    Validates / formats / sanitises the assistant's answer.
"""

from ai.config import get_llm_config
from ai.conversation_service import ConversationService

__all__ = [
    "get_llm_config",
    "ConversationService",
]
