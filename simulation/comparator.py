"""
simulation/comparator.py
Scenario comparison and scoring engine.

Compares multiple future outcomes across scenarios, calculates transparent
scores, and ranks them. Scoring is domain-aware and configurable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    name: str
    description: str
    is_baseline: bool
    input_params: dict[str, Any]
    output_metrics: dict[str, Any]
    time_series: list[dict]
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)


DEFAULT_WEIGHTS = {
    "finance": {
        "goal_achievement": 0.35,
        "financial_benefit": 0.30,
        "sustainability": 0.20,
        "risk_penalty": 0.15,
    },
    "study": {
        "performance_improvement": 0.40,
        "study_investment": 0.25,
        "sustainability": 0.20,
        "risk_penalty": 0.15,
    },
    "habits": {
        "fitness_improvement": 0.35,
        "habit_consistency": 0.30,
        "sustainability": 0.20,
        "risk_penalty": 0.15,
    },
}


def compare_scenarios(scenarios: list[ScenarioResult], domain: str) -> list[ScenarioResult]:
    """Score and rank all scenarios for a domain.

    Args:
        scenarios: List of ScenarioResult objects (unscored).
        domain: "finance", "study", or "habits".

    Returns:
        Same list, with scores and score_breakdown populated,
        sorted descending by total score.
    """
    if not scenarios:
        return []

    weights = DEFAULT_WEIGHTS.get(domain, DEFAULT_WEIGHTS["finance"])

    baseline = next((s for s in scenarios if s.is_baseline), None)
    baseline_metrics = baseline.output_metrics if baseline else {}

    for scenario in scenarios:
        breakdown = _compute_score_breakdown(scenario, baseline_metrics, domain, weights)
        scenario.score_breakdown = breakdown
        scenario.score = round(sum(breakdown.values()), 2)

    scenarios.sort(key=lambda s: s.score, reverse=True)

    logger.info(
        "Scenarios scored for %s: %s",
        domain,
        [(s.name, s.score) for s in scenarios],
    )
    return scenarios


def _compute_score_breakdown(
    scenario: ScenarioResult,
    baseline_metrics: dict,
    domain: str,
    weights: dict[str, float],
) -> dict[str, float]:
    """Compute individual score components for a scenario."""
    if domain == "finance":
        return _score_finance(scenario, baseline_metrics, weights)
    elif domain == "study":
        return _score_study(scenario, baseline_metrics, weights)
    elif domain == "habits":
        return _score_habits(scenario, baseline_metrics, weights)
    return {}


def _score_finance(scenario: ScenarioResult, baseline: dict, weights: dict) -> dict[str, float]:
    m = scenario.output_metrics

    goal_score = m.get("goal_score", 0)
    goal_component = (goal_score / 100.0) * 100.0 * weights.get("goal_achievement", 0.35)

    final_balance = m.get("final_balance", 0)
    base_balance = baseline.get("final_balance", final_balance)
    if base_balance > 0:
        benefit_ratio = max(0, (final_balance - base_balance) / abs(base_balance))
    else:
        benefit_ratio = 1.0 if final_balance > 0 else 0.0
    benefit_component = min(benefit_ratio * 100, 100) * weights.get("financial_benefit", 0.30)

    sustainable = m.get("sustainable", True)
    surplus = m.get("monthly_surplus", 0)
    if sustainable and surplus >= 0:
        sustainability = min(100, 50 + surplus * 0.5)
    elif sustainable:
        sustainability = 40
    else:
        sustainability = max(0, 20 + surplus * 0.3)
    sustain_component = sustainability * weights.get("sustainability", 0.20)

    risk = 0
    if not sustainable:
        risk += 60
    if surplus < -1000:
        risk += 40
    elif surplus < -500:
        risk += 20
    risk = min(100, risk)
    risk_component = (100 - risk) * weights.get("risk_penalty", 0.15)

    return {
        "goal_achievement": round(goal_component, 2),
        "financial_benefit": round(benefit_component, 2),
        "sustainability": round(sustain_component, 2),
        "risk_penalty": round(risk_component, 2),
    }


def _score_study(scenario: ScenarioResult, baseline: dict, weights: dict) -> dict[str, float]:
    m = scenario.output_metrics

    final_score = m.get("final_score", 0)
    base_score = baseline.get("final_score", final_score)
    improvement = final_score - base_score
    improvement_component = min(max(0, (improvement / max(100 - base_score, 1)) * 100), 100) * weights.get("performance_improvement", 0.40)

    hours = scenario.input_params.get("hours_per_day", 0)
    if hours <= 0:
        investment = 100
    elif hours <= 6:
        investment = max(0, 100 - (hours - 2) * 10)
    else:
        investment = max(0, 100 - hours * 12)
    investment_component = investment * weights.get("study_investment", 0.25)

    sustainability = min(100, 60 + (6 - min(hours, 8)) * 8)
    sustain_component = sustainability * weights.get("sustainability", 0.20)

    risk = 0
    if hours > 10:
        risk += 50
    elif hours > 8:
        risk += 25
    if improvement < 0:
        risk += 30
    risk = min(100, risk)
    risk_component = (100 - risk) * weights.get("risk_penalty", 0.15)

    return {
        "performance_improvement": round(improvement_component, 2),
        "study_investment": round(investment_component, 2),
        "sustainability": round(sustain_component, 2),
        "risk_penalty": round(risk_component, 2),
    }


def _score_habits(scenario: ScenarioResult, baseline: dict, weights: dict) -> dict[str, float]:
    m = scenario.output_metrics

    final_fitness = m.get("projected_fitness_score", 0)
    base_fitness = baseline.get("projected_fitness_score", final_fitness)
    fitness_improvement = final_fitness - base_fitness
    fitness_component = min(max(0, (fitness_improvement / max(100 - base_fitness, 1)) * 100), 100) * weights.get("fitness_improvement", 0.35)

    consistency = m.get("habit_consistency", 0)
    consistency_component = (consistency / 100.0) * 100 * weights.get("habit_consistency", 0.30)

    exercise_freq = m.get("exercise_frequency", 3)
    if exercise_freq <= 5:
        sustainability = 90 - exercise_freq * 2
    else:
        sustainability = max(30, 90 - exercise_freq * 8)
    sustain_component = sustainability * weights.get("sustainability", 0.20)

    risk = 0
    if exercise_freq > 6:
        risk += 40
    if consistency < 30:
        risk += 30
    risk = min(100, risk)
    risk_component = (100 - risk) * weights.get("risk_penalty", 0.15)

    return {
        "fitness_improvement": round(fitness_component, 2),
        "habit_consistency": round(consistency_component, 2),
        "sustainability": round(sustain_component, 2),
        "risk_penalty": round(risk_component, 2),
    }


def get_comparison_table(scenarios: list[ScenarioResult], domain: str) -> list[dict]:
    """Format scenario results as a comparison table for display."""
    table = []
    for s in scenarios:
        row = {
            "Scenario": s.name,
            "Score": s.score,
            "Baseline": "Yes" if s.is_baseline else "No",
        }
        if domain == "finance":
            row["Final Balance"] = s.output_metrics.get("final_balance", 0)
            row["Net Change"] = s.output_metrics.get("net_worth_change", 0)
            row["Monthly Surplus"] = s.output_metrics.get("monthly_surplus", 0)
            row["Goal Score"] = s.output_metrics.get("goal_score", 0)
            row["Sustainable"] = "Yes" if s.output_metrics.get("sustainable", True) else "No"
        elif domain == "study":
            row["Final Score"] = s.output_metrics.get("final_score", 0)
            row["Improvement"] = s.output_metrics.get("score_improvement", 0)
            row["Study Hours"] = s.output_metrics.get("total_study_hours", 0)
        elif domain == "habits":
            row["Fitness Score"] = s.output_metrics.get("projected_fitness_score", 0)
            row["Change"] = s.output_metrics.get("fitness_score_change", 0)
            row["Exercise Freq"] = s.output_metrics.get("exercise_frequency", 0)
            row["Consistency"] = s.output_metrics.get("habit_consistency", 0)

        table.append(row)
    return table
