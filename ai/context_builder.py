"""
ai/context_builder.py
Builds a controlled, structured Digital Twin context for the LLM.

The context contains only the relevant, already-computed information the LLM
needs to ground its answer - it does NOT pass raw database dumps or unrelated
records. This keeps API token usage small and stops the LLM from seeing (or
echoing) sensitive, irrelevant data.

The context is built exclusively from the user's own authenticated user_id, so
no other user's data can ever leak into another user's AI context.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

import database as db
from simulation.engine import run_simulation, SimulationRequest


@dataclass
class DigitalTwinContext:
    """Structured representation of the user's Digital Twin snapshot."""

    user_id: int
    profile: dict = field(default_factory=dict)
    financial: dict = field(default_factory=dict)
    study: dict = field(default_factory=dict)
    habits: dict = field(default_factory=dict)
    fitness: dict = field(default_factory=dict)
    goals: list = field(default_factory=list)
    simulations: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    # --- availability helpers (used by the UI to decide what to show) ---
    def has_finance(self) -> bool:
        return bool(self.financial and self.financial.get("total_savings", 0) != 0 or
                    self.financial.get("has_records", False))

    def has_study(self) -> bool:
        return bool(self.study and self.study.get("days_active", 0) > 0)

    def has_goals(self) -> bool:
        return bool(self.goals)

    def has_simulations(self) -> bool:
        return bool(self.simulations)

    def has_recommendations(self) -> bool:
        return bool(self.recommendations)

    def to_block(self) -> str:
        """Render the context as a compact, delimited text block for the LLM."""
        parts = ["[profile]", _fmt_json(self.profile) if self.profile else "No profile data."]
        parts.append("[financial]")
        parts.append(_fmt_json(self.financial) if self.financial else "No financial data.")
        parts.append("[study]")
        parts.append(_fmt_json(self.study) if self.study else "No study data.")
        parts.append("[habits]")
        parts.append(_fmt_json(self.habits) if self.habits else "No habit data.")
        parts.append("[fitness]")
        parts.append(_fmt_json(self.fitness) if self.fitness else "No fitness data.")
        parts.append("[goals]")
        parts.append(_fmt_json(self.goals) if self.goals else "[]")
        parts.append("[simulations]")
        parts.append(_fmt_json(self.simulations) if self.simulations else "[]")
        parts.append("[recommendations]")
        parts.append(_fmt_json(self.recommendations) if self.recommendations else "[]")
        return "\n".join(parts)


def _fmt_json(value: Any) -> str:
    try:
        return json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def build_context(user_id: int) -> DigitalTwinContext:
    """Build the Digital Twin context snapshot for the given user.

    Args:
        user_id: The authenticated user whose data should be gathered.

    Returns:
        A DigitalTwinContext populated only from the user's own data.
    """
    user = db.get_user(user_id) or {}

    # ---- Profile ----
    profile = {
        "name": user.get("name"),
        "age": user.get("age"),
        "occupation": user.get("occupation"),
        "gender": user.get("gender"),
        "days_active": db.get_days_active(user_id),
    }

    # ---- Financial ----
    fin = db.get_user_financial_summary(user_id)
    try:
        _, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)
    except Exception:
        projected_1yr, monthly_rate = 0.0, 0.0
    financial = {
        "monthly_income": fin.get("monthly_income", 0),
        "monthly_expenses": fin.get("monthly_expenses", 0),
        "monthly_savings": fin.get("monthly_savings", 0),
        "total_savings": fin.get("total_savings", 0),
        "monthly_savings_rate": monthly_rate,
        "savings_projection_12mo": projected_1yr,
    }

    # ---- Study ----
    study_summary = db.get_user_study_summary(user_id)
    study = {
        "avg_hours_per_day": study_summary.get("avg_hours_per_day", 0),
        "avg_performance_score": study_summary.get("avg_performance_score", 0),
        "subjects": study_summary.get("subjects", []),
        "days_active": study_summary.get("days_active", 0),
    }
    study_pred = _latest_prediction_result("study")
    if study_pred is not None:
        study["predicted_performance"] = study_pred

    # ---- Habits & Fitness ----
    summary = db.get_user_habit_summary(user_id)
    habits = {
        "avg_completion_rate": summary.get("avg_completion_rate", 0),
        "habit_names": summary.get("habit_names", []),
        "total_entries": summary.get("total_entries", 0),
    }
    fitness = {
        "avg_steps": summary.get("avg_steps", 0),
        "avg_exercise_minutes": summary.get("avg_exercise_minutes", 0),
        "avg_sleep_hours": summary.get("avg_sleep_hours", 0),
        "exercise_frequency": summary.get("exercise_frequency", 0),
    }

    # ---- Goals ----
    goals = _goals_to_simple(db.get_user_goals(user_id))

    # ---- Simulations & Recommendations (saved ones) ----
    simulations = _load_saved_simulations(user_id)
    recommendations = _load_cleaned_recommendations(user_id)

    ctx = DigitalTwinContext(
        user_id=user_id,
        profile=profile,
        financial=financial,
        study=study,
        habits=habits,
        fitness=fitness,
        goals=goals,
        simulations=simulations,
        recommendations=recommendations,
    )
    return ctx


def run_simulation_snapshot(user_id: int, domain: str, horizon_months: int = 12) -> dict:
    """Reuse the existing Milestone 3 engine to produce an on-demand snapshot.

    This lets the assistant answer "what happens if I increase my savings?"
    by running the real simulation engine and returning its grounded result -
    the LLM is never asked to redo the math.

    Args:
        user_id: authenticated user id.
        domain: one of "finance", "study", "habits".
        horizon_months: forecast horizon.

    Returns:
        The dict returned by ``run_simulation`` (scenarios, recommendation...).
    """
    params = {
        "financial": db.get_user_financial_summary(user_id),
        "study": db.get_user_study_summary(user_id),
        "habits": db.get_user_habit_summary(user_id),
        "goals": db.get_user_goals(user_id),
    }
    request = SimulationRequest(
        user_id=user_id,
        domain=domain,
        horizon_months=horizon_months,
        custom_params={},
    )
    return run_simulation(request, params)


def _latest_prediction_result(domain: str):
    """Best-effort read of the latest prediction value for a domain."""
    try:
        df = db.get_domain_predictions(f"{domain}_predictions", 0, limit=1)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    val = df.iloc[0].get("result_value")
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _goals_to_simple(goals) -> list:
    out = []
    for g in goals or []:
        out.append(
            {
                "goal_name": g.get("goal_name"),
                "target_amount": g.get("target_amount"),
                "current_progress": g.get("current_progress"),
                "target_date": g.get("target_date"),
            }
        )
    return out


def _load_saved_simulations(user_id: int) -> list:
    try:
        sims = db.get_simulations(user_id, limit=5)
    except Exception:
        return []
    if sims.empty:
        return []
    out = []
    for _, s in sims.head(5).iterrows():
        scenarios = db.get_simulation_scenarios(int(s["simulation_id"]))
        best = None
        best_score = 0.0
        if not scenarios.empty:
            top = scenarios.sort_values("score", ascending=False).iloc[0]
            best = top.get("scenario_name")
            try:
                best_score = float(top.get("score") or 0)
            except (TypeError, ValueError):
                best_score = 0.0
        out.append(
            {
                "title": s.get("title"),
                "domain": s.get("simulation_type"),
                "horizon_months": s.get("horizon_months"),
                "best_scenario": best,
                "best_score": best_score,
            }
        )
    return out


def _load_cleaned_recommendations(user_id: int) -> list:
    try:
        recs = db.get_recommendations(user_id, limit=5)
    except Exception:
        return []
    if recs.empty:
        return []
    out = []
    for _, r in recs.head(5).iterrows():
        out.append(
            {
                "category": r.get("category"),
                "priority": r.get("priority"),
                "recommendation_text": r.get("recommendation_text"),
                "reason": r.get("reason"),
                "risks": r.get("risks"),
                "next_action": r.get("next_action"),
            }
        )
    return out
