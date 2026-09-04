"""
ai/config.py
Environment / secrets driven configuration for the Conversational AI layer.

Supports Gemini as the primary AI provider, swappable at runtime through
environment variables, plus a built-in deterministic "rule_based" provider
that requires no API key (used as automatic fallback / offline / testing).

Never hardcode API keys here - read them from the environment or Streamlit
secrets. Example environment variables::

    LLM_PROVIDER=gemini
    GEMINI_API_KEY=...
    GEMINI_MODEL=gemini-3.7-flash

Secrets can also be supplied via ``.streamlit/secrets.toml`` under an ``[llm]``
section and will take precedence over environment variables.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

SUPPORTED_PROVIDERS = ("gemini", "rule_based")

DEFAULT_GEMINI_MODEL = "gemini-3.7-flash"


@dataclass(frozen=True)
class LLMConfig:
    """Resolved LLM provider configuration (all values validated)."""

    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 600
    timeout_seconds: int = 60
    rate_limit_retries: int = 2
    raw_env: dict = field(default_factory=dict, repr=False, compare=False)


def _read_secrets() -> dict:
    """Best-effort read of the ``[llm]`` section of Streamlit secrets.

    Importing Streamlit at module load in a plain python/pytest process can be
    slow but is guarded. Returns a dict of {key: value} or {}.
    """
    try:
        import streamlit as st

        secret_llm = st.secrets.get("llm", {})
        if isinstance(secret_llm, Mapping):
            return dict(secret_llm)
    except Exception:
        pass
    return {}


def _env_or_secret(env_key: str, secrets: dict, fallback: Optional[str] = None) -> Optional[str]:
    """Read a value from the environment first, then secrets, then fallback."""
    val = os.getenv(env_key)
    if val is None or val == "":
        val = secrets.get(env_key.lower()) or secrets.get(env_key)
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return fallback
    return os.getenv(env_key, val)


@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """Resolve and validate the LLM configuration.

    Raises:
        ValueError: if an unsupported provider is configured.
    """
    secrets = _read_secrets()

    provider = (os.getenv("LLM_PROVIDER") or secrets.get("provider") or "rule_based").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}."
        )

    api_key = _env_or_secret("GEMINI_API_KEY", secrets) if provider == "gemini" else None

    model = None
    if provider == "gemini":
        model = _env_or_secret("GEMINI_MODEL", secrets, DEFAULT_GEMINI_MODEL)

    temperature = _env_or_secret("LLM_TEMPERATURE", secrets, "0.3")
    max_tokens = _env_or_secret("LLM_MAX_TOKENS", secrets, "600")
    timeout_seconds = _env_or_secret("LLM_TIMEOUT_SECONDS", secrets, "60")
    rate_limit_retries = _env_or_secret("LLM_RATE_LIMIT_RETRIES", secrets, "2")

    def _to_float(v, default) -> float:
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _to_int(v, default) -> int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return default

    return LLMConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        temperature=_to_float(temperature, 0.3),
        max_tokens=_to_int(max_tokens, 600),
        timeout_seconds=_to_int(timeout_seconds, 60),
        rate_limit_retries=_to_int(rate_limit_retries, 2),
        raw_env=dict(os.environ),
    )


def has_valid_api_key(config: Optional[LLMConfig] = None) -> bool:
    """Return True if the configured provider can make a real LLM call.

    The rule-based provider never needs a key.
    """
    cfg = config or get_llm_config()
    if cfg.provider == "rule_based":
        return True
    return bool(cfg.api_key)


def require_api_key(config: Optional[LLMConfig] = None) -> bool:
    """Raise if a real provider is configured but the API key is missing.

    Returns True when valid. Used by the service so the UI can show a friendly
    "missing API key" message instead of a raw traceback.
    """
    cfg = config or get_llm_config()
    if cfg.provider != "rule_based" and not cfg.api_key:
        raise RuntimeError(
            f"Missing API key for LLM provider '{cfg.provider}'. "
            f"Set {cfg.provider.upper()}_API_KEY in the environment or "
            ".streamlit/secrets.toml, or switch LLM_PROVIDER=rule_based."
        )
    return True
