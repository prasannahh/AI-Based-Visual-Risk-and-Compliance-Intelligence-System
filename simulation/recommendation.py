"""
simulation/recommendation.py
Recommendation engine for the Digital Twin Simulation.

Receives scored scenario results and generates personalized
recommendations with reasons, trade-offs, and actionable next steps.
"""

from __future__ import annotations

import logging
from typing import Any

from simulation.comparator import ScenarioResult

logger = logging.getLogger(__name__)


def generate_recommendation(
    scenarios: list[ScenarioResult],
    domain: str,
    user_data: dict,
) -> dict[str, Any] | None:
    """Generate a personalized recommendation from scored scenarios.

    Args:
        scenarios: Scored and sorted scenario results.
        domain: "finance", "study", or "habits".
        user_data: Current user state from database.

    Returns:
        Dict with recommended scenario, reason, benefits, risks,
        and next_action. Returns None if no scenarios available.
    """
    if not scenarios:
        return None

    best = scenarios[0]
    baseline = next((s for s in scenarios if s.is_baseline), scenarios[-1])

    if domain == "finance":
        return _recommend_finance(best, baseline, scenarios, user_data)
    elif domain == "study":
        return _recommend_study(best, baseline, scenarios, user_data)
    elif domain == "habits":
        return _recommend_habits(best, baseline, scenarios, user_data)

    return None


def _recommend_finance(
    best: ScenarioResult,
    baseline: ScenarioResult,
    all_scenarios: list[ScenarioResult],
    user_data: dict,
) -> dict[str, Any]:
    reason_parts = []
    benefits = []
    risks = []
    next_actions = []

    best_m = best.output_metrics
    base_m = baseline.output_metrics

    balance_diff = best_m.get("final_balance", 0) - base_m.get("final_balance", 0)
    if balance_diff > 0:
        reason_parts.append(
            f"Projects a final balance of \u20b9{best_m['final_balance']:,.0f}, "
            f"\u20b9{balance_diff:,.0f} more than your current plan"
        )
        benefits.append(f"Increase of \u20b9{balance_diff:,.0f} in projected savings")

    if best_m.get("goal_score", 0) > base_m.get("goal_score", 0):
        reason_parts.append("Better progress toward your financial goals")
        benefits.append(f"Goal score improves from {base_m.get('goal_score', 0):.0f}% to {best_m.get('goal_score', 0):.0f}%")

    if best_m.get("sustainable") and not base_m.get("sustainable", True):
        reason_parts.append("More sustainable than your current plan")
        benefits.append("Maintains a positive monthly surplus")

    if best.input_params.get("monthly_expenses", 0) < baseline.input_params.get("monthly_expenses", 0):
        benefit_pct = round(
            (baseline.input_params["monthly_expenses"] - best.input_params["monthly_expenses"])
            / max(baseline.input_params["monthly_expenses"], 1) * 100, 1
        )
        benefits.append(f"Reduces monthly expenses by {benefit_pct}%")

    surplus = best_m.get("monthly_surplus", 0)
    if surplus < 0:
        risks.append(f"Monthly surplus is negative (\u20b9{surplus:,.0f}) — may be difficult to sustain")
    elif surplus < 2000:
        risks.append(f"Monthly surplus is low (\u20b9{surplus:,.0f}) — limited financial cushion")

    saving_rate = best.input_params.get("monthly_saving", 0)
    income = best.input_params.get("monthly_income", 1)
    if income > 0 and saving_rate / income > 0.6:
        risks.append("Saving more than 60% of income — may be hard to maintain long-term")

    if best.is_baseline:
        reason_parts.append("Your current plan is already the best option based on the analysis")
        next_actions.append("Continue following your current financial plan")
        next_actions.append("Review this simulation periodically as your income changes")
    else:
        next_actions.append(
            f"Adjust your monthly savings to \u20b9{best.input_params.get('monthly_saving', 0):,.0f}"
        )
        if best.input_params.get("monthly_expenses", 0) < baseline.input_params.get("monthly_expenses", 0):
            next_actions.append("Review spending categories for the largest reduction opportunities")
        next_actions.append("Set up automatic transfers to lock in the new savings amount")

    category = "finance"
    priority = "high" if balance_diff > 10000 else "medium"

    return {
        "recommended_scenario": best.name,
        "description": best.description,
        "reason": "; ".join(reason_parts) if reason_parts else f"Best overall score ({best.score:.1f}/100)",
        "benefits": benefits,
        "risks": risks,
        "next_actions": next_actions,
        "score": best.score,
        "baseline_comparison": {
            "baseline_name": baseline.name,
            "baseline_score": baseline.score,
            "improvement": round(best.score - baseline.score, 2),
        },
        "category": category,
        "priority": priority,
    }


def _recommend_study(
    best: ScenarioResult,
    baseline: ScenarioResult,
    all_scenarios: list[ScenarioResult],
    user_data: dict,
) -> dict[str, Any]:
    reason_parts = []
    benefits = []
    risks = []
    next_actions = []

    best_m = best.output_metrics
    base_m = baseline.output_metrics

    improvement = best_m.get("final_score", 0) - base_m.get("final_score", 0)

    if improvement > 0:
        reason_parts.append(
            f"Projects a final score of {best_m['final_score']:.1f}/100 "
            f"(+{improvement:.1f} improvement over baseline)"
        )
        benefits.append(f"Performance score improves by {improvement:.1f} points")
    else:
        reason_parts.append("Maintains or optimizes your study workload effectively")

    best_hours = best.input_params.get("hours_per_day", 0)
    base_hours = baseline.input_params.get("hours_per_day", 0)
    if best_hours > base_hours:
        benefits.append(f"Increases study time by {best_hours - base_hours:.1f} hours/day")

    total_hours = best_m.get("total_study_hours", 0)
    if total_hours > 400:
        risks.append(f"Total study load of {total_hours:.0f} hours may lead to burnout")
    if best_hours > 8:
        risks.append(f"{best_hours:.1f} hours/day is intensive — ensure adequate rest")

    if best.is_baseline:
        reason_parts.append("Your current study pattern is already well-optimized")
        next_actions.append("Maintain your current study routine")
        next_actions.append("Focus on study quality rather than increasing hours")
    else:
        next_actions.append(f"Aim for {best_hours:.1f} study hours per day")
        next_actions.append("Track study sessions to maintain consistency")
        next_actions.append("Schedule regular breaks to avoid burnout")

    return {
        "recommended_scenario": best.name,
        "description": best.description,
        "reason": "; ".join(reason_parts) if reason_parts else f"Best overall score ({best.score:.1f}/100)",
        "benefits": benefits,
        "risks": risks,
        "next_actions": next_actions,
        "score": best.score,
        "baseline_comparison": {
            "baseline_name": baseline.name,
            "baseline_score": baseline.score,
            "improvement": round(best.score - baseline.score, 2),
        },
        "category": "study",
        "priority": "high" if improvement > 5 else "medium",
    }


def _recommend_habits(
    best: ScenarioResult,
    baseline: ScenarioResult,
    all_scenarios: list[ScenarioResult],
    user_data: dict,
) -> dict[str, Any]:
    reason_parts = []
    benefits = []
    risks = []
    next_actions = []

    best_m = best.output_metrics
    base_m = baseline.output_metrics

    fitness_change = best_m.get("projected_fitness_score", 0) - base_m.get("projected_fitness_score", 0)

    if fitness_change > 0:
        reason_parts.append(
            f"Projects a fitness score of {best_m['projected_fitness_score']:.1f}/100 "
            f"(+{fitness_change:.1f} improvement)"
        )
        benefits.append(f"Fitness score improves by {fitness_change:.1f} points")

    best_freq = best_m.get("exercise_frequency", 0)
    base_freq = base_m.get("exercise_frequency", best_freq)
    if best_freq > base_freq:
        benefits.append(f"Increases exercise frequency from {base_freq} to {best_freq} days/week")

    consistency = best_m.get("habit_consistency", 0)
    if consistency > 70:
        benefits.append(f"Habit consistency projected at {consistency:.0f}%")

    steps_change = best_m.get("projected_avg_steps", 0) - base_m.get("projected_avg_steps", 0)
    if steps_change > 0:
        benefits.append(f"Average daily steps increase by {steps_change:,.0f}")

    if best_freq > 6:
        risks.append("Exercising 6-7 days/week may increase injury risk — include rest days")
    if fitness_change < 0:
        risks.append("This scenario may lead to a decrease in fitness metrics")

    if best.is_baseline:
        reason_parts.append("Your current habit pattern is already well-balanced")
        next_actions.append("Maintain your current routine")
        next_actions.append("Focus on consistency rather than intensity")
    else:
        if best_freq > base_freq:
            next_actions.append(f"Increase exercise to {best_freq} days/week")
        next_actions.append("Track daily habits to maintain the new pattern")
        next_actions.append("Set weekly reminders to stay on track")

    return {
        "recommended_scenario": best.name,
        "description": best.description,
        "reason": "; ".join(reason_parts) if reason_parts else f"Best overall score ({best.score:.1f}/100)",
        "benefits": benefits,
        "risks": risks,
        "next_actions": next_actions,
        "score": best.score,
        "baseline_comparison": {
            "baseline_name": baseline.name,
            "baseline_score": baseline.score,
            "improvement": round(best.score - baseline.score, 2),
        },
        "category": "habits",
        "priority": "high" if fitness_change > 5 else "medium",
    }
