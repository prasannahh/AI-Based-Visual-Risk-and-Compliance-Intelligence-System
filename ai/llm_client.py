"""
ai/llm_client.py
Provider-agnostic LLM client abstraction.

The application connects to Gemini (primary) or the built-in deterministic
rule-based fallback through a single ``LLMClient`` interface, so no other part
of the codebase is tightly coupled to one vendor.

The rule-based client is a structured, deterministic assistant that answers
Digital Twin questions directly from the provided context (no external model).
It keeps the app fully functional and unit-testable even when no API key is
configured, and it never invents data - it only reports what is in context.

When Gemini is configured but fails (missing key, API error, timeout, network
failure, rate limit, empty response), the conversation service automatically
falls back to the rule-based client without crashing.

All client implementations:
    - never log or echo the API key,
    - raise LLMError subclasses that the service maps to user-friendly messages,
    - accept a system prompt and a user message and return a plain-text answer.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from ai.config import LLMConfig, get_llm_config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base error for any LLM client failure."""


class LLMConfigurationError(LLMError):
    """Missing/invalid provider or API key."""


class LLMApiError(LLMError):
    """The upstream LLM API call failed (network, HTTP, timeout)."""


class LLMRateLimitError(LLMApiError):
    """The upstream provider throttled/rate-limited the request."""


class LLMResponseError(LLMError):
    """The provider returned an empty / unusable response."""


class LLMClient(ABC):
    """Common interface for all LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:  # pragma: no cover
        """Return the assistant's plain-text answer for the given messages."""


# --------------------------------------------------------------------------- #
# Gemini client (google-genai SDK)
# --------------------------------------------------------------------------- #
class GeminiClient(LLMClient):
    provider = "gemini"

    def complete(self, system_prompt: str, user_message: str) -> str:
        if not self.config.api_key:
            raise LLMConfigurationError(
                "Gemini provider selected but GEMINI_API_KEY is not set."
            )

        model_name = self.config.model or "gemini-3.7-flash"

        try:
            from google import genai  # type: ignore
            from google.genai import types
        except ImportError as exc:  # pragma: no cover
            raise LLMConfigurationError(
                "Gemini provider selected but google-genai is not installed. "
                "Run: pip install google-genai"
            ) from exc

        client = genai.Client(
            api_key=self.config.api_key,
            http_options=types.HttpOptions(
                timeout=self.config.timeout_seconds * 1000,
            ),
        )
        contents = [
            types.Content(role="user", parts=[types.Part(text=system_prompt)]),
            types.Content(role="user", parts=[types.Part(text=user_message)]),
        ]

        # Gemini 3.x Flash uses Thinking and does not accept the legacy
        # sampling parameters (temperature / top_p / top_k). Only generation
        # limits that the installed SDK/API still supports are passed.
        config = types.GenerateContentConfig(
            max_output_tokens=self.config.max_tokens,
        )

        last_error = None
        # Retry temporary Gemini errors (429, 503, quota, high demand, etc.)
        # up to the configured retry count before giving up and letting the
        # service fall back to the rule-based assistant.
        retries = max(1, int(getattr(self.config, "rate_limit_retries", 2) or 1))
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                return (response.text or "").strip()
            except Exception as exc:
                message = str(getattr(exc, "message", exc))
                last_error = exc
                temporary = (
                    "429" in message
                    or "resource_exhausted" in message
                    or "resource exhausted" in message
                    or "quota" in message.lower()
                    or "503" in message
                    or "service unavailable" in message.lower()
                    or "high demand" in message.lower()
                    or "temporarily" in message.lower()
                )
                if temporary and attempt < retries - 1:
                    delay = 0.5 * (attempt + 1)
                    logger.warning(
                        "Gemini request hit a temporary error (attempt %d/%d): "
                        "retrying in %.1fs.",
                        attempt + 1,
                        retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                break

        message = str(getattr(last_error, "message", last_error))
        if "429" in message or "resource_exhausted" in message or "quota" in message.lower():
            raise LLMRateLimitError("Gemini rate limit reached.") from last_error
        raise LLMApiError(f"Gemini API error: {message}") from last_error


# --------------------------------------------------------------------------- #
# Deterministic rule-based fallback - the source-of-truth narrator
# --------------------------------------------------------------------------- #
class RuleBasedClient(LLMClient):
    """Deterministic assistant that answers solely from context.

    It is a small intent router over the structured context_block produced by
    ``context_builder``. Because the context block already contains the
    engine-computed figures, this client produces accurate, grounded answers
    with no external model and no API key.
    """

    provider = "rule_based"

    def complete(self, system_prompt: str, user_message: str) -> str:  # noqa: C901
        # The context block is appended to the user_message by the service as
        # delimited JSON between markers. Pull it out if present.
        context, question = self._split_context(user_message)
        q = question.lower()

        lines = []
        self._add_heading(lines, "Personal Digital Twin Decision Assistant")

        if not context:
            lines.append(
                "I couldn't find any Digital Twin data for your account yet. "
                "Head to a data page and add some financial, study, habit or "
                "goal entries first - then I can give you grounded guidance."
            )
            return "\n".join(lines)

        sc = _SectionReader(context)

        if self._has_any(sc, ["financial", "finance", "saving", "spend", "income", "expense", "money", "budget"]):
            self._narrate_finance(lines, sc, q)
        if self._has_any(sc, ["study", "product", "score", "subject", "exam", "learn"]):
            self._narrate_study(lines, sc, q)
        if self._has_any(sc, ["habit", "routine", "consisten"]):
            self._narrate_habits(lines, sc, q)
        if self._has_any(sc, ["fitness", "exercise", "step", "sleep", "calorie", "walk", "weight"]):
            self._narrate_fitness(lines, sc, q)
        if self._has_any(sc, ["goal", "target"]):
            self._narrate_goals(lines, sc, q)
        if self._has_any(sc, ["simulation", "scenario", "recommend", "what if", "increase my saving", "best scenario", "biggest problem"]):
            self._narrate_simulation_recommendation(lines, sc, q)

        self._add_grounding_note(lines)
        return "\n".join(lines)

    # ---------------------- helpers ---------------------- #
    @staticmethod
    def _split_context(user_message: str):
        marker = "DIGITAL_TWIN_CONTEXT_BEGIN"
        end_marker = "DIGITAL_TWIN_CONTEXT_END"
        if marker in user_message and end_marker in user_message:
            start = user_message.index(marker) + len(marker)
            end = user_message.index(end_marker)
            context = user_message[start:end]
            question = user_message[end + len(end_marker):].strip()
            return context, question
        return "", user_message

    @staticmethod
    def _add_heading(lines, title):
        lines.append(f"**{title}**")
        lines.append("")

    @staticmethod
    def _add_grounding_note(lines):
        lines.append("")
        lines.append(
            "_Grounded in your Digital Twin data. Figures marked '(forecast)' or "
            "'(simulation)' are projections based on the current simulation, not "
            "guaranteed outcomes._"
        )

    @staticmethod
    def _has_any(sc, keys):
        return sc.has_any(keys)

    @staticmethod
    def _section(sc, name):
        return sc.read(name)

    def _narrate_finance(self, lines, sc, q):
        fin = self._section(sc, "financial")
        lines.append("**Finance**")
        if not fin:
            lines.append("- No financial data recorded yet.")
            return
        income = self._number(getattr(fin, "monthly_income", None))
        expenses = self._number(getattr(fin, "monthly_expenses", None))
        savings = self._number(getattr(fin, "monthly_savings", None))
        total = self._number(getattr(fin, "total_savings", None))
        projection = self._number(getattr(fin, "savings_projection_12mo", None))

        has_finance_data = any(v not in (None, 0) for v in (income, expenses, savings, total))
        if not has_finance_data:
            lines.append(
                "- No financial records have been added yet, so I don't have "
                "concrete income/expense/savings figures to ground an answer on. "
                "Head to a data page and log some financial entries first."
            )
            return

        lines.append(f"- Monthly income: **{self._rupee(income)}**")
        lines.append(f"- Monthly expenses: **{self._rupee(expenses)}**")
        lines.append(f"- Monthly savings: **{self._rupee(savings)}**")
        lines.append(f"- Total savings: **{self._rupee(total)}**")
        if projection is not None:
            lines.append(f"- 12-month savings projection (forecast): **{self._rupee(projection)}**")

        if "save" in q or "increase my saving" in q:
            yearly = self._num_or(savings, 0.0) * 12.0
            lines.append(
                f"- **Scenario impact:** At your current savings of {self._rupee(savings)}/month "
                f"you would add about {self._rupee(yearly)} over a year. Increasing it "
                "would raise the projected balance accordingly."
            )
        if "do financially" in q or "how am i doing" in q:
            ratio = (self._num_or(savings, 0.0) / self._num_or(income, 0.0) * 100) if self._num_or(income, 0.0) else 0.0
            lines.append(f"- Savings rate ~ **{ratio:.0f}%** of income.")

    def _narrate_study(self, lines, sc, q):
        lines.append("**Study & Productivity**")
        study = self._section(sc, "study")
        if not study:
            lines.append("- No study data recorded yet.")
            return
        hours = self._number(getattr(study, "avg_hours_per_day", None))
        score = self._number(getattr(study, "avg_performance_score", None))
        predicted = self._number(getattr(study, "predicted_performance", None))
        subjects = getattr(study, "subjects", [])
        lines.append(f"- Average study hours/day: **{hours if hours is not None else 'n/a'} h**")
        lines.append(f"- Average performance score: **{score if score is not None else 'n/a'}/100**")
        if subjects:
            lines.append(f"- Subjects tracked: {', '.join(subjects[:6])}")
        if predicted is not None:
            lines.append(f"- Predicted performance (forecast): **{predicted:.1f}/100**")
        if "improve" in q:
            if score is not None and score < 75:
                lines.append(
                    "- **Suggestion:** focus on consistency and your weakest subject; "
                    "the forecast/simulation should be your guide. Increase study hours "
                    "in the simulation page to see projected improvement."
                )
            else:
                lines.append("- Performance looks strong - maintain consistency and quality.")

    def _narrate_habits(self, lines, sc, q):
        lines.append("**Habits**")
        habits = self._section(sc, "habits")
        if not habits:
            lines.append("- No habit data recorded yet.")
            return
        names = getattr(habits, "habit_names", [])
        avg = self._number(getattr(habits, "avg_completion_rate", None))
        entries = getattr(habits, "total_entries", 0)
        lines.append(f"- Average habit completion: **{avg if avg is not None else 'n/a'}%**")
        if names:
            lines.append(f"- Habits tracked: {', '.join(names[:6])}")
        lines.append(f"- Habit entries logged: {entries}")
        if avg is not None:
            if avg >= 75:
                lines.append("- Consistency is strong - keep the streak going.")
            elif avg >= 45:
                lines.append("- Moderate consistency - small nudges could help.")
            else:
                lines.append("- Habit consistency is at risk - consider lighter, easier targets.")

    def _narrate_fitness(self, lines, sc, q):
        lines.append("**Fitness**")
        fitness = self._section(sc, "fitness")
        if not fitness:
            lines.append("- No fitness data recorded yet.")
            return
        steps = self._number(getattr(fitness, "avg_steps", None))
        exercise = self._number(getattr(fitness, "avg_exercise_minutes", None))
        sleep = self._number(getattr(fitness, "avg_sleep_hours", None))
        freq = getattr(fitness, "exercise_frequency", None)
        lines.append(f"- Average steps/day: **{self._int(steps)}**" if steps is not None else "- Average steps/day: n/a")
        lines.append(f"- Average exercise: **{exercise} min/day**" if exercise is not None else "- Average exercise: n/a")
        lines.append(f"- Average sleep: **{sleep} h**" if sleep is not None else "- Average sleep: n/a")
        if freq is not None:
            lines.append(f"- Exercise frequency: **{freq} days/week**")
        if steps is not None and steps < 5000:
            lines.append("- Activity is below the 5k-step/day mark - a gentle daily walk would help.")

    def _narrate_goals(self, lines, sc, q):
        lines.append("**Goals**")
        goals = sc.read_array("goals")
        if not goals:
            lines.append("- No goals set yet.")
            return
        for g in goals[:5]:
            name = g.get("goal_name", "Goal")
            target = self._number(g.get("target_amount", None))
            current = self._number(g.get("current_progress", None))
            if target is not None and current is not None:
                pct = (current / target * 100) if target else 0.0
                lines.append(f"- **{name}:** {self._rupee(current)} / {self._rupee(target)} ({pct:.0f}%)")
            elif target is not None:
                lines.append(f"- **{name}:** target {self._rupee(target)}")
            else:
                lines.append(f"- **{name}:** (no target recorded)")
        if "save enough for my goal" in q or "reach my goal" in q:
            lines.append(
                "- Whether you reach a goal depends on your savings projection (see Finance). "
                "Run a financial simulation in the Simulation page for a grounded projection."
            )

    def _narrate_simulation_recommendation(self, lines, sc, q):
        recs = sc.read_array("recommendations")
        if recs:
            lines.append("**Recommendations (from the recommendation engine)**")
            for r in recs[:5]:
                cat = r.get("category", "general")
                text = r.get("recommendation_text") or r.get("reason", "")
                priority = r.get("priority", "medium")
                lines.append(f"- [{cat} · {priority}] {text}")
        sims = sc.read_array("simulations")
        if sims:
            lines.append("**Latest simulation**")
            top = sims[0]
            name = top.get("title", "Simulation")
            lines.append(f"- {name}: top scenario '{top.get('best_scenario', 'n/a')}' "
                         f"score {top.get('best_score', 'n/a')}")
        if "best scenario" in q or "best for me" in q:
            if recs:
                lines.append("- Use the simulation page to compare scenarios; scores decide the best.")
            else:
                lines.append(
                    "- I don't have saved simulation results yet. Run a simulation first, "
                    "then compare the scenario scores to find the best for you."
                )

    @staticmethod
    def _number(value):
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _num_or(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(value):
        try:
            return f"{float(value):,.0f}"
        except (TypeError, ValueError):
            return "n/a"

    @staticmethod
    def _rupee(value):
        try:
            v = float(value)
            rounded = abs(v) >= 1000
            if rounded:
                return f"₹{v:,.0f}"
            return f"₹{v:,.2f}"
        except (TypeError, ValueError):
            return "n/a"


# --------------------------------------------------------------------------- #
# Simple context-section reader
# --------------------------------------------------------------------------- #
class _SectionReader:
    """Splits the delimited context block into named sections keyed by `[name]`.

    Each section body is parsed as JSON when possible (the context builder emits
    sections as JSON objects/arrays), otherwise as ``key: value`` lines so the
    rule-based client can still report values.
    """

    def __init__(self, text):
        import re

        self._sections = {}
        for match in re.finditer(r"\[([a-z_]+)\]\s*(.*?)(?=\n\[[a-z_]+\]|\Z)", text, re.DOTALL | re.IGNORECASE):
            name = match.group(1).lower().strip()
            body = match.group(2).strip()
            self._sections[name] = body

    def has_any(self, keys):
        return any(self.read(k) is not None for k in keys)

    def read(self, name):
        body = self._sections.get(name.lower())
        if body is None:
            return None
        return _Section(body)

    def read_array(self, name):
        return _parse_json_or_empty(self._sections.get(name.lower(), ""))

    def __bool__(self):
        return bool(self._sections)


def _parse_json_or_empty(text: str):
    """Parse a section body as JSON, returning a list (for arrays) or dict."""
    import json

    text = (text or "").strip()
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


class _Section:
    def __init__(self, text):
        self._text = (text or "").strip()
        self._attrs = {}
        # Prefer JSON object semantics when the body is a single JSON object.
        import json

        parsed = None
        if self._text.startswith("{"):
            try:
                parsed = json.loads(self._text)
            except json.JSONDecodeError:
                parsed = None
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                self._attrs[key.lower()] = value
                setattr(self, key, value)
        else:
            for line in self._text.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip().strip("'\"")
                    self._attrs[key] = value
                    setattr(self, key, value)

    def __getattr__(self, item):
        return self._attrs.get(item.lower())

    def __bool__(self):
        return bool(self._text)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def build_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Return the LLM client for the resolved configuration."""
    cfg = config or get_llm_config()
    client_cls = {
        "gemini": GeminiClient,
        "rule_based": RuleBasedClient,
    }.get(cfg.provider)
    if client_cls is None:
        raise LLMConfigurationError(f"Unsupported provider: {cfg.provider}")
    return client_cls(cfg)
