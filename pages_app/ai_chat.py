"""
pages_app/ai_chat.py
Conversational AI page - the Personal Digital Twin Decision Assistant.

Presents a clean chat interface with:
    - conversation history,
    - suggested questions,
    - loading indicator,
    - friendly error handling,
    - a reset-conversation option.

It talks through the ai.conversation_service, which grounds every answer in the
user's real Digital Twin data. When Gemini is configured but unavailable, the
service automatically falls back to the built-in rule-based assistant.
"""

from __future__ import annotations

import streamlit as st

import ai.prompt_templates as templates
from ai.config import has_valid_api_key, get_llm_config
from ai.conversation_service import ConversationService, ConversationError
from ai.llm_client import build_llm_client, LLMConfigurationError, LLMApiError, LLMRateLimitError
from ai.response_formatter import fallback_message

# Session keys used to persist the chat.
_HISTORY_KEY = "ai_chat_history"
_SERVICE_KEY = "ai_convo_service"


def _init_chat_state(user_id: int) -> None:
    if _SERVICE_KEY not in st.session_state or st.session_state[_SERVICE_KEY] is None:
        st.session_state[_SERVICE_KEY] = ConversationService(user_id)
    if _HISTORY_KEY not in st.session_state:
        st.session_state[_HISTORY_KEY] = []


def _reset_chat() -> None:
    st.session_state[_HISTORY_KEY] = []
    st.session_state.pop(_SERVICE_KEY, None)


def _provider_status() -> str:
    try:
        cfg = get_llm_config()
    except Exception as e:
        return f"⚠️ {e}"
    if cfg.provider == "rule_based":
        return "🧠 Mode: **built-in assistant** (no API key configured)"
    if cfg.provider == "gemini" and has_valid_api_key(cfg):
        return f"🤖 Provider: **Gemini** · model **{cfg.model}** (with automatic rule-based fallback)"
    if cfg.provider == "gemini" and not has_valid_api_key(cfg):
        return (
            "⚠️ Provider **Gemini** selected but its API key is missing. "
            "Answers will use the built-in grounded assistant until "
            "`GEMINI_API_KEY` is set."
        )
    return f"ℹ️ Provider: **{cfg.provider}**"


def _format_history_message(role: str, content: str) -> str:
    if role == "assistant":
        return content
    return content


def render():
    user_id = st.session_state.user_id
    _init_chat_state(user_id)
    service: ConversationService = st.session_state[_SERVICE_KEY]

    st.markdown("### 💬 Conversational AI Assistant")
    st.caption(
        "Your Personal Digital Twin Decision Assistant - every answer is grounded "
        "in your actual financial, study, habit, fitness and goal data."
    )

    with st.expander("ℹ️ Assistant status", expanded=True):
        st.markdown(_provider_status())
        st.caption(
            "The AI uses your real Digital Twin data and the app's forecasting, "
            "simulation and recommendation engines. It never invents numbers."
        )

    # ---------------------------- suggested questions ---------------------------- #
    with st.container(border=True):
        st.markdown("#### 💡 Suggested questions")
        cols = st.columns(2)
        for i, q in enumerate(templates.SUGGESTED_QUESTIONS):
            with cols[i % 2]:
                if st.button(q, key=f"sugg_{i}", use_container_width=True):
                    _ask(service, q)
                    st.rerun()

    # ------------------------------ conversation ------------------------------ #
    history = st.session_state[_HISTORY_KEY]
    for turn in history:
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])

    st.divider()

    prompt = st.chat_input("Ask about your Digital Twin...")
    if prompt:
        _ask(service, prompt.strip())
        st.rerun()

    # ------------------------------ reset option ------------------------------ #
    if history:
        if st.button("🔄 Reset conversation", use_container_width=True):
            _reset_chat()
            st.rerun()
    else:
        st.caption(templates.DEFAULT_GREETING)


def _ask(service: ConversationService, question: str) -> None:
    """Run one turn and append the result to chat history."""
    if not question:
        return
    history = st.session_state[_HISTORY_KEY]

    history.append({"role": "user", "question": question, "answer": None})
    st.session_state[_HISTORY_KEY] = history

    # The conversation_service handles the full flow: try primary provider,
    # fall back to rule-based if it fails. We just need to invoke it.
    with st.spinner("Analysing your Digital Twin..."):
        try:
            turn = service.answer(question, refresh_context=True)
            answer = turn.answer
            # Show provider info in the answer if fallback was used
            if turn.provider == "rule_based_fallback":
                answer = (
                    f"_[Using rule-based assistant (Gemini unavailable)]_\n\n"
                    f"{answer}"
                )
        except ConversationError as e:
            _, msg = service.describe_error(e)
            answer = msg
        except (LLMApiError, LLMRateLimitError) as e:
            _, msg = service.describe_error(e)
            answer = msg
        except LLMConfigurationError as e:
            answer = f"Configuration error: {e}\n\n{fallback_message()}"
        except Exception:
            # Never show a raw traceback to the user.
            answer = fallback_message()

    if not answer:
        answer = fallback_message()

    history.append({
        "role": "assistant",
        "question": question,
        "answer": answer,
    })
    st.session_state[_HISTORY_KEY] = history
