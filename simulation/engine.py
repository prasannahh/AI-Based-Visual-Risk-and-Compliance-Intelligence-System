"""
simulation/engine.py
Central Digital Twin Simulation Engine.

Receives user state + decision parameters, generates multiple scenarios,
computes future outcomes for each, and returns structured results.

All numerical calculations are deterministic Python/backend logic —
no LLM calls for computation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from simulation.scenarios import (
    generate_financial_scenarios,
    generate_study_scenarios,
    generate_habit_scenarios,
)
from simulation.comparator import compare_scenarios, ScenarioResult
from simulation.recommendation import generate_recommendation

logger = logging.getLogger(__name__)


@dataclass
class SimulationRequest:
    user_id: int
    domain: str  # "finance", "study", "habits"
    horizon_months: int = 12
    custom_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    simulation_id: int | None
    domain: str
    horizon_months: int
    scenarios: list[ScenarioResult]
    recommendation: dict[str, Any] | None
    baseline_label: str


def run_financial_simulation(
    user_id: int,
    monthly_income: float,
    monthly_expenses: float,
    current_savings: float,
    monthly_saving: float,
    horizon_months: int,
    goals: list[dict] | None = None,
    custom_scenarios: list[dict] | None = None,
) -> list[ScenarioResult]:
    """Simulate financial decisions across multiple scenarios.

    Args:
        user_id: Authenticated user ID.
        monthly_income: Current monthly income.
        monthly_expenses: Current monthly expenses.
        current_savings: Current total savings balance.
        monthly_saving: Current monthly savings amount.
        horizon_months: Forecast horizon in months.
        goals: Optional list of financial goals.
        custom_scenarios: Optional user-defined scenario overrides.

    Returns:
        List of ScenarioResult objects.
    """
    logger.info("Financial simulation started for user %s, horizon %d months", user_id, horizon_months)

    scenarios = generate_financial_scenarios(
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_saving=monthly_saving,
        current_savings=current_savings,
        custom_scenarios=custom_scenarios,
    )

    results = []
    for scenario in scenarios:
        outcome = _simulate_financial_scenario(
            monthly_income=monthly_income,
            monthly_expenses=scenario["monthly_expenses"],
            monthly_saving=scenario["monthly_saving"],
            current_savings=current_savings,
            horizon_months=horizon_months,
            goals=goals or [],
        )
        results.append(
            ScenarioResult(
                name=scenario["name"],
                description=scenario["description"],
                is_baseline=scenario.get("is_baseline", False),
                input_params={
                    "monthly_income": monthly_income,
                    "monthly_expenses": scenario["monthly_expenses"],
                    "monthly_saving": scenario["monthly_saving"],
                },
                output_metrics=outcome["metrics"],
                time_series=outcome["time_series"],
                score=0.0,  # filled by comparator
            )
        )

    logger.info("Financial simulation completed: %d scenarios generated", len(results))
    return results


def _simulate_financial_scenario(
    monthly_income: float,
    monthly_expenses: float,
    monthly_saving: float,
    current_savings: float,
    horizon_months: int,
    goals: list[dict],
) -> dict:
    """Deterministic financial projection for one scenario."""
    balance = current_savings
    total_savings = 0.0
    total_expenses = 0.0
    total_income = 0.0
    time_series = []
    goal_achievement_month = None
    monthly_surplus = monthly_income - monthly_expenses - monthly_saving

    for month in range(1, horizon_months + 1):
        balance += monthly_saving
        total_savings += monthly_saving
        total_expenses += monthly_expenses
        total_income += monthly_income

        time_series.append({
            "month": month,
            "balance": round(balance, 2),
            "cumulative_savings": round(total_savings, 2),
            "monthly_expenses": round(monthly_expenses, 2),
        })

        if goal_achievement_month is None and goals:
            for goal in goals:
                target = goal.get("target_amount", 0)
                current = goal.get("current_progress", 0)
                if target > 0 and balance >= target - current:
                    goal_achievement_month = month
                    break

    sustainable = monthly_surplus >= 0
    remaining_after_expenses = monthly_surplus

    goal_score = 0.0
    if goals:
        goal_scores = []
        for goal in goals:
            target = goal.get("target_amount", 0)
            current = goal.get("current_progress", 0)
            if target > 0:
                progress_pct = min(balance / (target - current), 1.0) if (target - current) > 0 else 1.0
                goal_scores.append(progress_pct * 100)
        goal_score = sum(goal_scores) / len(goal_scores) if goal_scores else 0.0

    metrics = {
        "final_balance": round(balance, 2),
        "total_savings_added": round(total_savings, 2),
        "total_expenses": round(total_expenses, 2),
        "total_income": round(total_income, 2),
        "net_worth_change": round(balance - current_savings, 2),
        "monthly_surplus": round(remaining_after_expenses, 2),
        "sustainable": sustainable,
        "goal_score": round(goal_score, 1),
        "goal_achievement_month": goal_achievement_month,
    }

    return {"metrics": metrics, "time_series": time_series}


def run_study_simulation(
    user_id: int,
    current_hours: float,
    current_score: float,
    subjects: list[str],
    horizon_months: int,
    consistency: float = 0.6,
    custom_scenarios: list[dict] | None = None,
) -> list[ScenarioResult]:
    """Simulate study decisions across multiple scenarios.

    Uses the Milestone 2 performance prediction model to estimate
    future scores under different study-hour scenarios.
    """
    logger.info("Study simulation started for user %s, horizon %d months", user_id, horizon_months)

    scenarios = generate_study_scenarios(
        current_hours=current_hours,
        custom_scenarios=custom_scenarios,
    )

    results = []
    for scenario in scenarios:
        hours = scenario["hours_per_day"]
        outcome = _simulate_study_scenario(
            hours_per_day=hours,
            current_score=current_score,
            subjects=subjects,
            horizon_months=horizon_months,
            consistency=consistency,
        )
        results.append(
            ScenarioResult(
                name=scenario["name"],
                description=scenario["description"],
                is_baseline=scenario.get("is_baseline", False),
                input_params={"hours_per_day": hours, "consistency": consistency},
                output_metrics=outcome["metrics"],
                time_series=outcome["time_series"],
                score=0.0,
            )
        )

    logger.info("Study simulation completed: %d scenarios generated", len(results))
    return results


def _simulate_study_scenario(
    hours_per_day: float,
    current_score: float,
    subjects: list[str],
    horizon_months: int,
    consistency: float,
) -> dict:
    """Deterministic study projection for one scenario.

    Uses the existing ML performance predictor when available,
    falls back to a linear projection model.
    """
    projected_scores = []
    score = current_score
    time_series = []

    try:
        from ai_models.study import predict as study_ai
        has_model = True
    except Exception:
        has_model = False

    for month in range(1, horizon_months + 1):
        if has_model and subjects:
            subject = subjects[0] if subjects else "Maths"
            days_left = max((horizon_months - month) * 30, 1)
            try:
                result = study_ai.predict_performance(
                    subject, hours_per_day, days_left, consistency, score
                )
                score = result["predicted_score"]
            except Exception:
                improvement_rate = (hours_per_day / 4.0 - 1.0) * 2.0
                score = min(100.0, score + improvement_rate)
        else:
            improvement_rate = (hours_per_day / 4.0 - 1.0) * 2.0
            score = min(100.0, score + improvement_rate)

        score = max(0.0, min(100.0, score))
        projected_scores.append(score)
        time_series.append({
            "month": month,
            "projected_score": round(score, 1),
            "hours_per_day": hours_per_day,
        })

    total_study_hours = hours_per_day * 30 * horizon_months
    improvement = score - current_score
    consistency_score = min(100, consistency * 100)

    metrics = {
        "final_score": round(score, 1),
        "score_improvement": round(improvement, 1),
        "total_study_hours": round(total_study_hours, 1),
        "consistency_score": round(consistency_score, 1),
        "avg_projected_score": round(sum(projected_scores) / len(projected_scores), 1) if projected_scores else 0.0,
    }

    return {"metrics": metrics, "time_series": time_series}


def run_habit_simulation(
    user_id: int,
    current_completion_rate: float,
    exercise_frequency: int,
    avg_steps: float,
    avg_sleep_hours: float,
    horizon_months: int,
    custom_scenarios: list[dict] | None = None,
) -> list[ScenarioResult]:
    """Simulate habit/fitness decisions across multiple scenarios.

    Projects future habit consistency and fitness metrics based on
    increased exercise frequency and improved habits.
    """
    logger.info("Habit simulation started for user %s, horizon %d months", user_id, horizon_months)

    scenarios = generate_habit_scenarios(
        current_completion_rate=current_completion_rate,
        exercise_frequency=exercise_frequency,
        custom_scenarios=custom_scenarios,
    )

    results = []
    for scenario in scenarios:
        outcome = _simulate_habit_scenario(
            completion_rate=scenario["completion_rate"],
            exercise_frequency=scenario["exercise_frequency"],
            avg_steps=avg_steps,
            avg_sleep_hours=avg_sleep_hours,
            horizon_months=horizon_months,
        )
        results.append(
            ScenarioResult(
                name=scenario["name"],
                description=scenario["description"],
                is_baseline=scenario.get("is_baseline", False),
                input_params={
                    "completion_rate": scenario["completion_rate"],
                    "exercise_frequency": scenario["exercise_frequency"],
                },
                output_metrics=outcome["metrics"],
                time_series=outcome["time_series"],
                score=0.0,
            )
        )

    logger.info("Habit simulation completed: %d scenarios generated", len(results))
    return results


def _simulate_habit_scenario(
    completion_rate: float,
    exercise_frequency: int,
    avg_steps: float,
    avg_sleep_hours: float,
    horizon_months: int,
) -> dict:
    """Deterministic habit/fitness projection for one scenario."""
    fitness_score = _compute_fitness_score(exercise_frequency, avg_steps, avg_sleep_hours, completion_rate)
    time_series = []
    cumulative_improvement = 0.0

    for month in range(1, horizon_months + 1):
        monthly_improvement = (exercise_frequency / 7.0) * 2.0 + (completion_rate / 100.0) * 1.5
        cumulative_improvement += monthly_improvement
        projected_score = min(100.0, fitness_score + cumulative_improvement * 0.3)

        projected_steps = avg_steps * (1 + (exercise_frequency - 3) * 0.05)
        projected_sleep = min(9.0, avg_sleep_hours + (exercise_frequency - 3) * 0.05)

        time_series.append({
            "month": month,
            "projected_fitness_score": round(projected_score, 1),
            "projected_steps": round(max(0, projected_steps), 0),
            "projected_sleep": round(min(12.0, max(4.0, projected_sleep)), 1),
        })

    final_score = time_series[-1]["projected_fitness_score"] if time_series else fitness_score
    final_steps = time_series[-1]["projected_steps"] if time_series else avg_steps
    final_sleep = time_series[-1]["projected_sleep"] if time_series else avg_sleep_hours

    habit_consistency = min(100.0, completion_rate * (1 + exercise_frequency * 0.02))

    metrics = {
        "projected_fitness_score": round(final_score, 1),
        "fitness_score_change": round(final_score - fitness_score, 1),
        "projected_avg_steps": round(final_steps, 0),
        "projected_sleep_hours": round(final_sleep, 1),
        "habit_consistency": round(habit_consistency, 1),
        "exercise_frequency": exercise_frequency,
    }

    return {"metrics": metrics, "time_series": time_series}


def _compute_fitness_score(exercise_frequency: int, avg_steps: float, avg_sleep: float, completion_rate: float) -> float:
    """Simple deterministic fitness score from current metrics."""
    freq_score = min(100, exercise_frequency / 7.0 * 100)
    steps_score = min(100, avg_steps / 10000.0 * 100)
    sleep_score = min(100, avg_sleep / 8.0 * 100)
    habit_score = completion_rate
    return round(freq_score * 0.3 + steps_score * 0.25 + sleep_score * 0.25 + habit_score * 0.2, 1)


def run_simulation(request: SimulationRequest, user_data: dict) -> dict:
    """High-level simulation dispatcher.

    Args:
        request: Simulation request with domain, horizon, and params.
        user_data: Current user state from database.

    Returns:
        Dict with scenarios, scores, and recommendation.
    """
    if request.domain == "finance":
        fin = user_data.get("financial", {})
        scenarios = run_financial_simulation(
            user_id=request.user_id,
            monthly_income=fin.get("monthly_income", 0),
            monthly_expenses=fin.get("monthly_expenses", 0),
            current_savings=fin.get("total_savings", 0),
            monthly_saving=fin.get("monthly_savings", 0),
            horizon_months=request.horizon_months,
            goals=user_data.get("goals", []),
            custom_scenarios=request.custom_params.get("scenarios"),
        )
    elif request.domain == "study":
        study = user_data.get("study", {})
        scenarios = run_study_simulation(
            user_id=request.user_id,
            current_hours=study.get("avg_hours_per_day", 0),
            current_score=study.get("avg_performance_score", 0),
            subjects=study.get("subjects", []),
            horizon_months=request.horizon_months,
            consistency=request.custom_params.get("consistency", 0.6),
            custom_scenarios=request.custom_params.get("scenarios"),
        )
    elif request.domain == "habits":
        habits = user_data.get("habits", {})
        scenarios = run_habit_simulation(
            user_id=request.user_id,
            current_completion_rate=habits.get("avg_completion_rate", 0),
            exercise_frequency=habits.get("exercise_frequency", 3),
            avg_steps=habits.get("avg_steps", 5000),
            avg_sleep_hours=habits.get("avg_sleep_hours", 7),
            horizon_months=request.horizon_months,
            custom_scenarios=request.custom_params.get("scenarios"),
        )
    else:
        raise ValueError(f"Unknown simulation domain: {request.domain}")

    scored_scenarios = compare_scenarios(scenarios, request.domain)
    recommendation = generate_recommendation(scored_scenarios, request.domain, user_data)

    return {
        "scenarios": scored_scenarios,
        "recommendation": recommendation,
        "domain": request.domain,
        "horizon_months": request.horizon_months,
    }
