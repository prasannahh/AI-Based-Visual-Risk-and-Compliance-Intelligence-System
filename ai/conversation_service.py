"""
ai/conversation_service.py
Orchestrates a single conversation turn for the Digital Twin Decision Assistant.

Flow:
    1. Build the grounded context for the authenticated user.
    2. Resolve the LLM config + client.
    3. Compose the user prompt (grounded context delimiters + question).
    4. Call the LLM (with friendly error mapping).
    5. If Gemini fails, automatically fall back to the rule-based client.
    6. Validate / format the response.

The service never sends raw database state to the model - only the curated
context built by ``context_builder``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import ai.prompt_templates as templates
from ai.config import LLMConfig, get_llm_config, has_valid_api_key
from ai.context_builder import build_context, DigitalTwinContext
from ai.llm_client import (
    LLMClient,
    LLMConfigurationError,
    LLMApiError,
    LLMRateLimitError,
    LLMResponseError,
    RuleBasedClient,
    build_llm_client,
)
from ai.response_formatter import (
    fallback_message,
    validate_response,
)

logger = logging.getLogger(__name__)


@dataclass
class ChatTurn:
    """A single Q/A exchange."""

    question: str
    answer: str
    provider: str
    model: Optional[str] = None
    grounded: bool = True
    context: Optional[DigitalTwinContext] = field(default=None, repr=False)


class ConversationService:
    """High-level conversational entry point used by the Streamlit chat UI."""

    def __init__(self, user_id: int, client: Optional[LLMClient] = None):
        self.user_id = user_id
        self._client = client  # optional injection for tests
        self._context_cache: Optional[DigitalTwinContext] = None

    def context(self, refresh: bool = False) -> DigitalTwinContext:
        """Return the current user's context (cached for the turn unless refresh)."""
        if refresh or self._context_cache is None:
            self._context_cache = build_context(self.user_id)
        return self._context_cache

    def _get_client(self) -> LLMClient:
        if self._client is not None:
            return self._client
        return build_llm_client(get_llm_config())

    def _get_fallback_client(self) -> RuleBasedClient:
        """Build a rule-based client for automatic fallback."""
        fallback_config = LLMConfig(provider="rule_based")
        return RuleBasedClient(fallback_config)

    def answer(self, question: str, refresh_context: bool = True) -> ChatTurn:
        """Answer a user question grounded in the user's Digital Twin.

        When the primary provider (Gemini) is unavailable or fails, the service
        automatically falls back to the rule-based deterministic assistant.

        Args:
            question: the user's natural-language question.
            refresh_context: rebuild context for this turn (default True so it
                reflects the latest data).

        Returns:
            A ChatTurn with the assistant's (validated) answer.

        Raises:
            ConversationError: for user/application-level problems (empty
                question, empty context, etc.).
        """
        if not question or not str(question).strip():
            raise ConversationError("Please enter a question.")

        ctx = self.context(refresh=refresh_context)

        # Determine the primary client.
        client = None
        primary_failed = False
        try:
            client = self._get_client()
        except Exception as exc:
            logger.warning("Failed to build primary LLM client: %s", exc)
            primary_failed = True

        provider_tag = getattr(client, "provider", None) if client else None

        # Case 1: The nominal provider is the rule-based assistant. Use it
        # directly - no Gemini call and no fallback marker (it's the explicit
        # rule_based mode, not a fallback from a failing provider).
        if provider_tag == "rule_based" and not primary_failed:
            return self._answer_with_client(question, ctx, client)

        # Case 2: Gemini (or any real provider) could not even be built
        # (missing key / SDK / config). Drop to the fallback assistant but mark
        # it as a fallback so the UI can be transparent about provider status.
        if primary_failed:
            fallback = self._get_fallback_client()
            turn = self._answer_with_client(question, ctx, fallback)
            turn.provider = "rule_based_fallback"
            return turn

        # Case 3: Gemini (or any real provider) was built. Try it first; if it
        # succeeds return the answer, otherwise automatically fall back.
        try:
            turn = self._answer_with_client(question, ctx, client)
            return turn
        except Exception as exc:
            logger.warning(
                "Primary provider '%s' failed (%s: %s). Falling back to rule-based.",
                provider_tag,
                type(exc).__name__,
                exc,
            )
            fallback = self._get_fallback_client()
            turn = self._answer_with_client(question, ctx, fallback)
            # Mark that fallback was used so the UI can display it.
            turn.provider = "rule_based_fallback"
            return turn

    def _answer_with_client(
        self, question: str, ctx: DigitalTwinContext, client: LLMClient
    ) -> ChatTurn:
        """Use a specific client to answer the question."""
        user_prompt = templates.build_user_prompt(question, ctx.to_block())
        raw = client.complete(templates.SYSTEM_PROMPT, user_prompt)

        cleaned = validate_response(raw)
        if cleaned is None:
            raise ConversationError("empty_response")

        provider = getattr(client, "provider", "unknown")
        model = getattr(client, "config", None)
        model_name = getattr(model, "model", None)

        return ChatTurn(
            question=question,
            answer=cleaned,
            provider=provider,
            model=model_name,
            grounded=True,
            context=ctx,
        )

    # ---------------------- friendly error mapping ---------------------- #
    @staticmethod
    def describe_error(exc: Exception) -> tuple[str, str]:
        """Map an exception to a (user_message, log_message) pair.

        Returns a short layer tag either 'info', 'warning' or 'error'.
        """
        if isinstance(exc, LLMConfigurationError):
            return ("config", str(exc))
        if isinstance(exc, LLMRateLimitError):
            return ("rate", "Rate limit reached. Please wait a moment and try again.")
        if isinstance(exc, LLMApiError):
            return ("api", "The AI service could not be reached right now. Please try again.")
        if isinstance(exc, LLMResponseError):
            return ("response", "The AI returned an unusable response. Please rephrase.")
        if isinstance(exc, ConversationError):
            msg = str(exc)
            if msg == "empty_response":
                return ("response", fallback_message("response"))
            return ("info", msg)
        return ("error", "An unexpected error occurred while preparing your answer.")


class ConversationError(Exception):
    """Raised for user/application-level conversation problems."""


# Keep a module-level helper so the UI can create one instance per user easily.
def create_conversation_service(user_id: int, client: Optional[LLMClient] = None) -> ConversationService:
    return ConversationService(user_id, client=client)
