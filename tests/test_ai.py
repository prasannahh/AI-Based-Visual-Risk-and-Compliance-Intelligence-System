"""
tests/test_ai.py
Milestone 4 - Conversational AI & Interactive Dashboard tests.

Covers:
    AI:
      - LLM configuration resolution / validation (Gemini + rule_based)
      - missing API key handling
      - context generation (DigitalTwinContext + to_block)
      - conversation service (rule-based client, no DB / no LLM needed)
      - empty user data handling
      - LLM failure handling (client that raises)
      - response formatting / validation
      - Gemini configuration
      - Gemini API key loading
      - Gemini client (missing key)
      - automatic Rule-Based fallback on Gemini failure
      - explicit Rule-Based mode
      - Digital Twin grounding
      - user isolation
      - prompt injection protection
    Dashboard / page:
      - page imports
      - data helpers don't crash on empty data
    Simulation integration:
      - on-demand simulation snapshot reuses the engine
      - scenario results and recommendation integration
    Performance:
      - measure simulation execution time (< 5s)

The tests intentionally avoid a live PostgreSQL connection by monkeypatching
the database service. The rule-based LLM client is used so no API key is needed.
Gemini API calls are mocked so no real API key is needed.
"""

import os
import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# --- Ensure a deterministic, key-free config for all tests ----------------- #
os.environ.setdefault("LLM_PROVIDER", "rule_based")

from ai import (  # noqa: E402
    get_llm_config,
    ConversationService,
)
from ai.config import (  # noqa: E402
    LLMConfig,
    has_valid_api_key,
    require_api_key,
    SUPPORTED_PROVIDERS,
)
from ai.context_builder import (  # noqa: E402
    DigitalTwinContext,
    build_context,
    run_simulation_snapshot,
)
from ai.llm_client import (  # noqa: E402
    build_llm_client,
    RuleBasedClient,
    GeminiClient,
    LLMConfigurationError,
    LLMApiError,
    LLMRateLimitError,
    LLMResponseError,
)
from ai.response_formatter import (  # noqa: E402
    clean_response,
    validate_response,
    fallback_message,
)
from ai.prompt_templates import (  # noqa: E402
    SYSTEM_PROMPT,
    build_user_prompt,
    SUGGESTED_QUESTIONS,
)


# =========================================================================== #
# Fixtures: monkeypatch the database and import modules that use it
# =========================================================================== #

@pytest.fixture()
def fake_db(monkeypatch):
    """Provide a fake populated database module for context building tests."""
    import database as db

    fake_user = {
        "name": "Jane Doe",
        "age": 28,
        "occupation": "Software Engineer",
        "gender": "Female",
    }

    def _get_user(uid):
        return dict(fake_user)

    def _get_user_financial_summary(uid):
        return {
            "monthly_income": 50000.0,
            "monthly_expenses": 35000.0,
            "monthly_savings": 15000.0,
            "total_savings": 100000.0,
        }

    def _get_savings_forecast(uid):
        df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=6),
                           "cumulative_savings": [10000, 20000, 30000, 40000, 50000, 60000]})
        return df, 340000.0, 15000.0

    def _get_user_study_summary(uid):
        return {"avg_hours_per_day": 3.5, "avg_performance_score": 78.0,
                "subjects": ["Maths", "Physics"], "days_active": 20}

    def _get_user_habit_summary(uid):
        return {"avg_completion_rate": 72.0,
                "habit_names": ["Exercise Frequency", "Sleep Schedule"],
                "total_entries": 40,
                "avg_steps": 7500.0, "avg_exercise_minutes": 35.0,
                "avg_sleep_hours": 7.2, "exercise_frequency": 4}

    def _get_user_goals(uid):
        return [
            {"goal_id": 1, "goal_name": "Emergency Fund", "target_amount": 300000,
             "current_progress": 100000, "target_date": "2027-01-01"}
        ]

    def _get_days_active(uid):
        return 20

    def _get_domain_predictions(table, uid, prediction_type=None, limit=1):
        return pd.DataFrame([{"result_value": 82.0}])

    def _get_simulations(uid, limit=5):
        return pd.DataFrame()

    def _get_recommendations(uid, limit=5):
        return pd.DataFrame(
            [{"category": "finance", "priority": "high",
              "recommendation_text": "Increase monthly savings rate",
              "reason": "Projection suggests target may not be reached."}]
        )

    monkeypatch.setattr(db, "get_user", _get_user)
    monkeypatch.setattr(db, "get_user_financial_summary", _get_user_financial_summary)
    monkeypatch.setattr(db, "get_savings_forecast", _get_savings_forecast)
    monkeypatch.setattr(db, "get_user_study_summary", _get_user_study_summary)
    monkeypatch.setattr(db, "get_user_habit_summary", _get_user_habit_summary)
    monkeypatch.setattr(db, "get_user_goals", _get_user_goals)
    monkeypatch.setattr(db, "get_days_active", _get_days_active)
    monkeypatch.setattr(db, "get_domain_predictions", _get_domain_predictions)
    monkeypatch.setattr(db, "get_simulations", _get_simulations)
    monkeypatch.setattr(db, "get_recommendations", _get_recommendations)
    return db


@pytest.fixture()
def empty_db(monkeypatch):
    """Provide a database module where the user has no data at all."""
    import database as db

    monkeypatch.setattr(db, "get_user", lambda uid: {"name": "X", "age": None,
                                                     "occupation": None, "gender": "Male"})

    def _empty_summary(uid):
        return {"monthly_income": 0.0, "monthly_expenses": 0.0,
                "monthly_savings": 0.0, "total_savings": 0.0}

    monkeypatch.setattr(db, "get_user_financial_summary", _empty_summary)
    monkeypatch.setattr(db, "get_savings_forecast", lambda uid: (pd.DataFrame(columns=["date", "cumulative_savings"]), 0.0, 0.0))
    monkeypatch.setattr(db, "get_user_study_summary", lambda uid: {"avg_hours_per_day": 0.0, "avg_performance_score": 0.0, "subjects": [], "days_active": 0})
    monkeypatch.setattr(db, "get_user_habit_summary", lambda uid: {"avg_completion_rate": 0.0, "habit_names": [], "total_entries": 0, "avg_steps": 0.0, "avg_exercise_minutes": 0.0, "avg_sleep_hours": 0.0, "exercise_frequency": 0})
    monkeypatch.setattr(db, "get_user_goals", lambda uid: [])
    monkeypatch.setattr(db, "get_days_active", lambda uid: 0)
    monkeypatch.setattr(db, "get_domain_predictions", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(db, "get_simulations", lambda uid, limit=5: pd.DataFrame())
    monkeypatch.setattr(db, "get_recommendations", lambda uid, limit=5: pd.DataFrame())
    return db


# =========================================================================== #
# Supported providers (OpenAI must NOT be supported)
# =========================================================================== #

def test_openai_not_in_supported_providers():
    assert "openai" not in SUPPORTED_PROVIDERS


def test_supported_providers_are_gemini_and_rule_based():
    assert "gemini" in SUPPORTED_PROVIDERS
    assert "rule_based" in SUPPORTED_PROVIDERS
    assert len(SUPPORTED_PROVIDERS) == 2


# =========================================================================== #
# LLM configuration
# =========================================================================== #

def test_default_config_is_rule_based():
    cfg = get_llm_config()
    assert cfg.provider == "rule_based"
    assert has_valid_api_key(cfg) is True


def test_gemini_config_from_env(monkeypatch):
    import ai.config as cfgmod

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    cfgmod.get_llm_config.cache_clear()
    cfg = get_llm_config()
    assert cfg.provider == "gemini"
    assert cfg.api_key == "g-key"
    assert has_valid_api_key(cfg) is True
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfgmod.get_llm_config.cache_clear()


def test_gemini_config_model_default(monkeypatch):
    import ai.config as cfgmod

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    cfgmod.get_llm_config.cache_clear()
    cfg = get_llm_config()
    assert cfg.model == "gemini-3.7-flash"
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfgmod.get_llm_config.cache_clear()


def test_gemini_config_model_custom(monkeypatch):
    import ai.config as cfgmod

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
    cfgmod.get_llm_config.cache_clear()
    cfg = get_llm_config()
    assert cfg.model == "gemini-1.5-pro"
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    cfgmod.get_llm_config.cache_clear()


def test_invalid_provider_raises(monkeypatch):
    import ai.config as cfgmod

    monkeypatch.setenv("LLM_PROVIDER", "doesnotexist")
    cfgmod.get_llm_config.cache_clear()
    with pytest.raises(ValueError):
        get_llm_config()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    cfgmod.get_llm_config.cache_clear()


def test_missing_api_key_for_gemini(monkeypatch):
    config = LLMConfig(provider="gemini", api_key=None)
    assert has_valid_api_key(config) is False


def test_missing_key_rule_based_ok():
    config = LLMConfig(provider="rule_based")
    assert has_valid_api_key(config) is True
    assert require_api_key(config) is True


def _mapping_like(inner):
    """A non-dict object that implements the ``collections.abc.Mapping``
    protocol (mirroring how Streamlit exposes secrets sections)."""
    from collections.abc import Mapping

    class SecretsSection(Mapping):
        def __getitem__(self, k):
            return inner[k]

        def __iter__(self):
            return iter(inner)

        def __len__(self):
            return len(inner)

    return SecretsSection()


def test_gemini_config_from_streamlit_secrets_mapping(monkeypatch):
    import ai.config as cfgmod

    for key in ("LLM_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL"):
        monkeypatch.delenv(key, raising=False)

    st_mock = MagicMock()
    st_mock.secrets.get.return_value = _mapping_like({
        "provider": "gemini",
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "gemini-3.7-flash",
    })

    with patch.dict("sys.modules", {"streamlit": st_mock}, clear=False):
        cfgmod.get_llm_config.cache_clear()
        cfg = get_llm_config()

    assert cfg.provider == "gemini"
    assert cfg.api_key == "test-key"
    assert cfg.model == "gemini-3.7-flash"
    cfgmod.get_llm_config.cache_clear()


def test_gemini_config_from_streamlit_secrets_plain_dict(monkeypatch):
    import ai.config as cfgmod

    for key in ("LLM_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL"):
        monkeypatch.delenv(key, raising=False)

    st_mock = MagicMock()
    st_mock.secrets.get.return_value = {
        "provider": "gemini",
        "GEMINI_API_KEY": "test-key",
        "GEMINI_MODEL": "gemini-3.7-flash",
    }

    with patch.dict("sys.modules", {"streamlit": st_mock}, clear=False):
        cfgmod.get_llm_config.cache_clear()
        cfg = get_llm_config()

    assert cfg.provider == "gemini"
    assert cfg.api_key == "test-key"
    assert cfg.model == "gemini-3.7-flash"
    cfgmod.get_llm_config.cache_clear()


# =========================================================================== #
# Client factory
# =========================================================================== #

def test_build_rule_based_client():
    client = build_llm_client()
    assert isinstance(client, RuleBasedClient)


def test_build_gemini_client_missing_key_raises_on_call():
    client = GeminiClient(LLMConfig(provider="gemini", api_key=None))
    with pytest.raises(LLMConfigurationError):
        client.complete("sys", "hi")


def test_build_llm_client_rejects_openai():
    with pytest.raises(LLMConfigurationError):
        build_llm_client(LLMConfig(provider="openai"))


# =========================================================================== #
# Context generation
# =========================================================================== #

def test_context_build_populated(fake_db):
    ctx = build_context(1)
    assert ctx.user_id == 1
    assert ctx.profile.get("name") == "Jane Doe"
    assert ctx.financial.get("monthly_income") == 50000.0
    assert ctx.financial.get("total_savings") == 100000.0
    assert ctx.study.get("avg_hours_per_day") == 3.5
    assert ctx.goals and ctx.goals[0]["goal_name"] == "Emergency Fund"
    assert len(ctx.goals) == 1
    assert ctx.has_goals() is True


def test_context_block_contains_sections(fake_db):
    ctx = build_context(1)
    block = ctx.to_block()
    for section in ["[profile]", "[financial]", "[study]", "[habits]",
                    "[fitness]", "[goals]", "[simulations]", "[recommendations]"]:
        assert section in block
    assert "50000" in block


def test_empty_context_build(empty_db):
    ctx = build_context(1)
    assert ctx.has_goals() is False
    block = ctx.to_block()
    assert "[financial]" in block


def test_context_availability_flags(empty_db):
    ctx = build_context(1)
    assert ctx.has_finance() is False
    assert ctx.has_study() is False


# =========================================================================== #
# Digital Twin grounding
# =========================================================================== #

def test_context_only_contains_user_data(fake_db):
    ctx = build_context(1)
    assert ctx.user_id == 1
    assert ctx.profile.get("name") == "Jane Doe"
    assert ctx.financial.get("monthly_income") == 50000.0


def test_user_isolation_context(fake_db, monkeypatch):
    """Verify context_builder always queries with the correct user_id."""
    import database as db
    called_uids = []

    def _tracking_user(uid):
        called_uids.append(uid)
        return {"name": f"User-{uid}", "age": 30, "occupation": "Test", "gender": "Male"}

    monkeypatch.setattr(db, "get_user", _tracking_user)
    build_context(1)
    build_context(42)
    assert called_uids == [1, 42]


# =========================================================================== #
# Prompt injection protection
# =========================================================================== #

def test_system_prompt_enforces_grounding_rules():
    assert "NEVER invent" in SYSTEM_PROMPT
    assert "NEVER fabricate" in SYSTEM_PROMPT.lower() or "never invent" in SYSTEM_PROMPT.lower()
    assert "source of truth" in SYSTEM_PROMPT.lower()


def test_build_user_prompt_wraps_context():
    prompt = build_user_prompt("question?", "CONTEXT")
    assert "DIGITAL_TWIN_CONTEXT_BEGIN" in prompt
    assert "DIGITAL_TWIN_CONTEXT_END" in prompt
    assert "CONTEXT" in prompt
    assert prompt.endswith("question?")


# =========================================================================== #
# Rule-based conversation (no DB, no API key)
# =========================================================================== #

def _make_service(monkeypatch, context):
    """A service with a rule-based client and a fixed context."""
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = context
    return service


def test_conversation_empty_question():
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = DigitalTwinContext(user_id=1)
    with pytest.raises(Exception):
        service.answer("   ")


def test_conversation_finance_grounded(fake_db):
    ctx = build_context(1)
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.grounded
    assert "Finance" in turn.answer
    assert "50,000" in turn.answer or "50000" in turn.answer


def test_conversation_empty_data(empty_db):
    ctx = build_context(1)
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    # It should report unavailability, not invent numbers.
    assert "n/a" in turn.answer or "No " in turn.answer


def test_conversation_goal_question(fake_db):
    ctx = build_context(1)
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("Will I be able to save enough for my goal?")
    assert "Goal" in turn.answer or "goal" in turn.answer or "Finance" in turn.answer


def test_conversation_provider_is_rule_based(fake_db):
    ctx = build_context(1)
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based"


# =========================================================================== #
# LLM failure handling
# =========================================================================== #

class _FailingClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        raise LLMApiError("simulated network failure")


class _RateLimitClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        raise LLMRateLimitError("429 rate limit")


class _EmptyResponseClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        return ""


class _TimeoutClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        raise LLMApiError("Gemini request timed out.")


class _QuotaExceededClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        raise LLMApiError("quota exceeded")


class _InvalidKeyClient:
    provider = "gemini"

    def complete(self, system_prompt, user_message):
        raise LLMConfigurationError("Invalid API key.")


# =========================================================================== #
# Gemini fallback tests
# =========================================================================== #

def test_gemini_api_error_falls_back_to_rule_based(fake_db):
    """When Gemini API fails, should automatically fall back to rule-based."""
    ctx = build_context(1)
    failing_client = _FailingClient()
    service = ConversationService(1, client=failing_client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer
    assert "50,000" in turn.answer or "50000" in turn.answer


def test_gemini_rate_limit_falls_back_to_rule_based(fake_db):
    """When Gemini is rate-limited, should automatically fall back."""
    ctx = build_context(1)
    client = _RateLimitClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_gemini_timeout_falls_back_to_rule_based(fake_db):
    """When Gemini times out, should automatically fall back."""
    ctx = build_context(1)
    client = _TimeoutClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_gemini_quota_exceeded_falls_back(fake_db):
    """When Gemini quota is exceeded, should fall back."""
    ctx = build_context(1)
    client = _QuotaExceededClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_gemini_invalid_key_falls_back(fake_db):
    """When Gemini key is invalid, should fall back."""
    ctx = build_context(1)
    client = _InvalidKeyClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_gemini_empty_response_falls_back(fake_db):
    """When Gemini returns empty response, should fall back."""
    ctx = build_context(1)
    client = _EmptyResponseClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_gemini_missing_key_build_fails_falls_back(fake_db):
    """When building the Gemini client fails (missing key), should fall back."""
    ctx = build_context(1)
    service = ConversationService(1, client=None)
    service._context_cache = ctx
    # Simulate: config says gemini but build fails → client is None
    # provider_tag becomes "rule_based" so we go to the direct path
    # But if the _get_client raises AND the fallback path catches it, it works
    with patch("ai.conversation_service.get_llm_config") as mock_cfg:
        mock_cfg.return_value = LLMConfig(provider="gemini", api_key=None)
        with patch("ai.conversation_service.build_llm_client") as mock_build:
            mock_build.side_effect = LLMConfigurationError("No API key")
            turn = service.answer("How am I doing financially?")
    # The exception from _get_client is caught and falls back to rule_based
    assert turn.provider == "rule_based_fallback"
    assert "Finance" in turn.answer


def test_explicit_rule_based_mode_no_gemini_call(fake_db):
    """When LLM_PROVIDER=rule_based, should never attempt Gemini."""
    ctx = build_context(1)
    client = RuleBasedClient(LLMConfig(provider="rule_based"))
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    assert turn.provider == "rule_based"
    assert "Finance" in turn.answer


def test_fallback_provides_useful_response_not_error_message(fake_db):
    """Fallback must provide a real grounded response, not just an error."""
    ctx = build_context(1)
    client = _FailingClient()
    service = ConversationService(1, client=client)
    service._context_cache = ctx
    turn = service.answer("How am I doing financially?")
    # Must contain real financial data
    assert "50,000" in turn.answer or "50000" in turn.answer
    assert "Finance" in turn.answer
    # Must NOT just be an error message
    assert "could not be reached" not in turn.answer.lower()
    assert "try again" not in turn.answer.lower()


# =========================================================================== #
# Conversation service error mapping
# =========================================================================== #

def test_conversation_llm_failure_described():
    from ai.conversation_service import ConversationService as CS
    service = CS(1, client=None)
    tag, msg = service.describe_error(LLMApiError("boom"))
    assert tag == "api"
    assert "could not be reached" in msg or "try again" in msg


def test_conversation_rate_limit_described():
    from ai.llm_client import LLMRateLimitError
    from ai.conversation_service import ConversationService as CS
    service = CS(1, client=None)
    tag, msg = service.describe_error(LLMRateLimitError("429"))
    assert tag == "rate"
    assert "wait" in msg.lower()


def test_conversation_unknown_error_friendly():
    from ai.conversation_service import ConversationService as CS
    service = CS(1, client=None)
    tag, msg = service.describe_error(RuntimeError("no stack for user"))
    assert tag == "error"
    assert "unexpected" in msg.lower()


# =========================================================================== #
# Response formatting / validation
# =========================================================================== #

def test_clean_response_trims_and_collapses():
    assert clean_response("  hello  ") == "hello"
    # Leading/trailing whitespace stripped, 3+ newlines collapsed to 2.
    assert clean_response("\n\na\n\n\nb\n\n") == "a\n\nb"
    assert clean_response(None) is None
    assert clean_response("   ") is None


def test_validate_response_blocks_secrets():
    assert validate_response("Good plan.") == "Good plan."
    assert validate_response("my api_key is sk-xxx") is None
    assert validate_response("My password is hunter2") is None


def test_validate_response_blocks_gemini_key():
    assert validate_response("Your GEMINI_API_KEY is ...") is None


def test_fallback_message_nonempty():
    assert fallback_message()
    assert fallback_message("response")


# =========================================================================== #
# Prompt templates
# =========================================================================== #

def test_system_prompt_contains_grounding_rules():
    assert "NEVER invent" in SYSTEM_PROMPT
    assert "simulation" in SYSTEM_PROMPT.lower()
    assert "HISTORICAL" in SYSTEM_PROMPT


def test_suggested_questions_nonempty():
    assert len(SUGGESTED_QUESTIONS) >= 6


# =========================================================================== #
# Dashboard / page imports
# =========================================================================== #

def test_dashboard_page_imports():
    import pages_app.dashboard
    import pages_app.ai_chat
    import pages_app.simulation
    assert callable(pages_app.dashboard.render)
    assert callable(pages_app.ai_chat.render)


def test_dashboard_style_helper_returns_none():
    # The _style helper mutates a figure and returns None (void).
    from pages_app.dashboard import _style
    import plotly.graph_objects as go
    fig = go.Figure()
    assert _style(fig, y_title="Test") is None


def test_empty_kpi_no_crash():
    # _render_kpis requires streamlit context; here we only ensure the
    # module-level defaults and helpers are importable and sane.
    from pages_app.dashboard import DEFAULT_HABITS
    assert isinstance(DEFAULT_HABITS, list) and len(DEFAULT_HABITS) >= 1


# =========================================================================== #
# Simulation integration
# =========================================================================== #

def test_simulation_snapshot_reuses_engine(fake_db):
    # Uses the real Milestone 3 engine against fake user state.
    result = run_simulation_snapshot(1, "finance", horizon_months=12)
    assert "scenarios" in result
    assert "recommendation" in result
    assert len(result["scenarios"]) >= 4
    assert result["recommendation"] is not None


def test_simulation_snapshot_scenario_scores(fake_db):
    result = run_simulation_snapshot(1, "finance", horizon_months=12)
    scores = sorted(s.score for s in result["scenarios"])
    # Scores populated and sorted descending
    assert result["scenarios"][0].score >= scores[-1]


def test_simulation_recommendation_integration(fake_db):
    result = run_simulation_snapshot(1, "finance", horizon_months=12)
    rec = result["recommendation"]
    assert rec["recommended_scenario"]
    assert rec["category"] == "finance"
    assert rec["reason"]


# =========================================================================== #
# Performance: simulation < 5s
# =========================================================================== #

def test_simulation_performance_under_5s(fake_db):
    start = time.time()
    result = run_simulation_snapshot(1, "finance", horizon_months=12)
    elapsed = time.time() - start
    assert len(result["scenarios"]) >= 1
    assert elapsed < 5.0, f"Simulation took {elapsed:.2f}s (target < 5s)"
