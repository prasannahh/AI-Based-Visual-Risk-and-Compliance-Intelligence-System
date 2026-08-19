"""Tests for the Digital Twin Recommendation Engine (Milestone 3)."""

from simulation.comparator import ScenarioResult, compare_scenarios
from simulation.engine import (
    run_financial_simulation,
    run_habit_simulation,
    run_study_simulation,
)
from simulation.recommendation import generate_recommendation


def _make_financial_scenarios():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    return compare_scenarios(scenarios, "finance")


def _make_study_scenarios():
    scenarios = run_study_simulation(
        user_id=1,
        current_hours=3.0,
        current_score=65.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    return compare_scenarios(scenarios, "study")


def _make_habit_scenarios():
    scenarios = run_habit_simulation(
        user_id=1,
        current_completion_rate=60,
        exercise_frequency=3,
        avg_steps=7000,
        avg_sleep_hours=7,
        horizon_months=6,
    )
    return compare_scenarios(scenarios, "habits")


# ---------------------------------------------------------------------------
# Best scenario selection tests
# ---------------------------------------------------------------------------

def test_recommendation_selects_best_scenario():
    scenarios = _make_financial_scenarios()
    rec = generate_recommendation(scenarios, "finance", {})
    assert rec is not None
    assert rec["recommended_scenario"] == scenarios[0].name
    assert rec["score"] == scenarios[0].score


def test_recommendation_study_best():
    scenarios = _make_study_scenarios()
    rec = generate_recommendation(scenarios, "study", {})
    assert rec is not None
    assert rec["recommended_scenario"] == scenarios[0].name


def test_recommendation_habits_best():
    scenarios = _make_habit_scenarios()
    rec = generate_recommendation(scenarios, "habits", {})
    assert rec is not None
    assert rec["recommended_scenario"] == scenarios[0].name


# ---------------------------------------------------------------------------
# Recommendation structure tests
# ---------------------------------------------------------------------------

def test_recommendation_has_required_fields():
    scenarios = _make_financial_scenarios()
    rec = generate_recommendation(scenarios, "finance", {})
    assert "recommended_scenario" in rec
    assert "reason" in rec
    assert "benefits" in rec
    assert "risks" in rec
    assert "next_actions" in rec
    assert "score" in rec
    assert "baseline_comparison" in rec
    assert "category" in rec
    assert "priority" in rec


def test_recommendation_reason_is_nonempty():
    scenarios = _make_financial_scenarios()
    rec = generate_recommendation(scenarios, "finance", {})
    assert len(rec["reason"]) > 0


def test_recommendation_benefits_is_list():
    scenarios = _make_financial_scenarios()
    rec = generate_recommendation(scenarios, "finance", {})
    assert isinstance(rec["benefits"], list)
    assert len(rec["benefits"]) > 0


def test_recommendation_baseline_comparison():
    scenarios = _make_financial_scenarios()
    rec = generate_recommendation(scenarios, "finance", {})
    bc = rec["baseline_comparison"]
    assert "baseline_name" in bc
    assert "baseline_score" in bc
    assert "improvement" in bc


# ---------------------------------------------------------------------------
# Risk-aware recommendation tests
# ---------------------------------------------------------------------------

def test_risk_aware_recommendation_finance():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=30000,
        monthly_expenses=25000,
        current_savings=50000,
        monthly_saving=20000,
        horizon_months=12,
    )
    scored = compare_scenarios(scenarios, "finance")
    rec = generate_recommendation(scored, "finance", {})
    assert rec is not None
    assert isinstance(rec["risks"], list)


def test_sustainable_scenario_preferred():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    scored = compare_scenarios(scenarios, "finance")
    rec = generate_recommendation(scored, "finance", {})
    assert rec is not None
    assert rec["category"] == "finance"


# ---------------------------------------------------------------------------
# Personalized recommendation tests
# ---------------------------------------------------------------------------

def test_recommendation_with_goals():
    goals = [{"goal_name": "House Fund", "target_amount": 500000, "current_progress": 100000}]
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=24,
        goals=goals,
    )
    scored = compare_scenarios(scenarios, "finance")
    rec = generate_recommendation(scored, "finance", {"goals": goals})
    assert rec is not None
    assert len(rec["benefits"]) > 0


def test_recommendation_different_domains():
    for domain, scenarios_fn in [
        ("finance", _make_financial_scenarios),
        ("study", _make_study_scenarios),
        ("habits", _make_habit_scenarios),
    ]:
        scenarios = scenarios_fn()
        rec = generate_recommendation(scenarios, domain, {})
        assert rec is not None
        assert rec["category"] == domain
        assert rec["recommended_scenario"]
        assert rec["reason"]


# ---------------------------------------------------------------------------
# Empty scenario handling
# ---------------------------------------------------------------------------

def test_recommendation_empty_scenarios():
    rec = generate_recommendation([], "finance", {})
    assert rec is None


def test_recommendation_single_scenario():
    scenarios = [ScenarioResult(
        name="Only Option",
        description="The only scenario",
        is_baseline=True,
        input_params={"monthly_saving": 15000},
        output_metrics={"final_balance": 280000, "sustainable": True, "goal_score": 50, "monthly_surplus": 5000},
        time_series=[],
    )]
    rec = generate_recommendation(scenarios, "finance", {})
    assert rec is not None
    assert rec["recommended_scenario"] == "Only Option"


def test_recommendation_baseline_only():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    baseline_only = [s for s in scenarios if s.is_baseline]
    scored = compare_scenarios(baseline_only, "finance")
    rec = generate_recommendation(scored, "finance", {})
    assert rec is not None
    assert "Current Plan" in rec["recommended_scenario"]
