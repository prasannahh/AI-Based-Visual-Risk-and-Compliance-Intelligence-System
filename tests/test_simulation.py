"""Tests for the Digital Twin Simulation Engine (Milestone 3)."""

import pandas as pd

from simulation.comparator import ScenarioResult, compare_scenarios, get_comparison_table
from simulation.engine import (
    SimulationRequest,
    _compute_fitness_score,
    _simulate_financial_scenario,
    _simulate_habit_scenario,
    _simulate_study_scenario,
    run_financial_simulation,
    run_habit_simulation,
    run_simulation,
    run_study_simulation,
)
from simulation.scenarios import (
    generate_financial_scenarios,
    generate_habit_scenarios,
    generate_study_scenarios,
)


# ---------------------------------------------------------------------------
# Scenario generation tests
# ---------------------------------------------------------------------------

def test_generate_financial_scenarios_baseline():
    scenarios = generate_financial_scenarios(
        monthly_income=50000,
        monthly_expenses=35000,
        monthly_saving=15000,
        current_savings=100000,
    )
    assert len(scenarios) >= 4  # baseline + 3 alternatives
    assert scenarios[0]["is_baseline"] is True
    assert scenarios[0]["name"] == "Current Plan"
    assert scenarios[0]["monthly_saving"] == 15000


def test_generate_financial_scenarios_custom():
    custom = [{"name": "Custom A", "monthly_saving": 20000, "monthly_expenses": 30000}]
    scenarios = generate_financial_scenarios(
        monthly_income=50000,
        monthly_expenses=35000,
        monthly_saving=15000,
        current_savings=100000,
        custom_scenarios=custom,
    )
    assert len(scenarios) == 2
    assert scenarios[1]["name"] == "Custom A"
    assert scenarios[1]["monthly_saving"] == 20000


def test_generate_study_scenarios_baseline():
    scenarios = generate_study_scenarios(current_hours=3.0)
    assert len(scenarios) >= 4
    assert scenarios[0]["is_baseline"] is True
    assert scenarios[0]["hours_per_day"] == 3.0


def test_generate_study_scenarios_custom():
    custom = [{"name": "Intense", "hours_per_day": 8.0}]
    scenarios = generate_study_scenarios(current_hours=3.0, custom_scenarios=custom)
    assert len(scenarios) == 2
    assert scenarios[1]["hours_per_day"] == 8.0


def test_generate_habit_scenarios_baseline():
    scenarios = generate_habit_scenarios(current_completion_rate=60, exercise_frequency=3)
    assert len(scenarios) >= 4
    assert scenarios[0]["is_baseline"] is True
    assert scenarios[0]["exercise_frequency"] == 3


def test_generate_habit_scenarios_custom():
    custom = [{"name": "Full Send", "completion_rate": 95, "exercise_frequency": 6}]
    scenarios = generate_habit_scenarios(
        current_completion_rate=60, exercise_frequency=3, custom_scenarios=custom
    )
    assert len(scenarios) == 2
    assert scenarios[1]["exercise_frequency"] == 6


# ---------------------------------------------------------------------------
# Financial simulation tests
# ---------------------------------------------------------------------------

def test_financial_baseline_simulation():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    assert len(results) >= 4
    baseline = next(s for s in results if s.is_baseline)
    assert baseline.output_metrics["final_balance"] == 100000 + 15000 * 12
    assert baseline.output_metrics["total_income"] == 50000 * 12
    assert baseline.output_metrics["total_expenses"] == 35000 * 12
    assert baseline.output_metrics["sustainable"] is True
    assert len(baseline.time_series) == 12


def test_financial_increased_savings():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    baseline = next(s for s in results if s.is_baseline)
    increased = next(s for s in results if s.name == "Save +25%")
    assert increased.output_metrics["final_balance"] > baseline.output_metrics["final_balance"]


def test_financial_expense_reduction():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    expense_scenario = next(s for s in results if s.name == "Cut Expenses 15%")
    assert expense_scenario.input_params["monthly_expenses"] < 35000
    assert expense_scenario.input_params["monthly_saving"] > 15000


def test_financial_goal_tracking():
    goals = [{"goal_name": "Emergency Fund", "target_amount": 300000, "current_progress": 100000}]
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
        goals=goals,
    )
    baseline = next(s for s in results if s.is_baseline)
    assert baseline.output_metrics["goal_score"] > 0


def test_financial_sustainability_flag():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=30000,
        monthly_expenses=25000,
        current_savings=50000,
        monthly_saving=20000,
        horizon_months=6,
    )
    unsustainable = [s for s in results if not s.output_metrics["sustainable"]]
    assert len(unsustainable) > 0


def test_financial_multiple_horizons():
    for horizon in [6, 12, 24]:
        results = run_financial_simulation(
            user_id=1,
            monthly_income=50000,
            monthly_expenses=35000,
            current_savings=100000,
            monthly_saving=15000,
            horizon_months=horizon,
        )
        assert all(len(s.time_series) == horizon for s in results)


# ---------------------------------------------------------------------------
# Study simulation tests
# ---------------------------------------------------------------------------

def test_study_baseline_simulation():
    results = run_study_simulation(
        user_id=1,
        current_hours=3.0,
        current_score=65.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    assert len(results) >= 4
    baseline = next(s for s in results if s.is_baseline)
    assert "final_score" in baseline.output_metrics
    assert len(baseline.time_series) == 6


def test_study_increased_hours():
    results = run_study_simulation(
        user_id=1,
        current_hours=3.0,
        current_score=65.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    baseline = next(s for s in results if s.is_baseline)
    more_hours = [s for s in results if not s.is_baseline and s.input_params["hours_per_day"] > 3.0]
    assert len(more_hours) > 0
    assert more_hours[0].input_params["hours_per_day"] > baseline.input_params["hours_per_day"]


def test_study_score_bounds():
    results = run_study_simulation(
        user_id=1,
        current_hours=5.0,
        current_score=90.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    for s in results:
        assert 0 <= s.output_metrics["final_score"] <= 100


# ---------------------------------------------------------------------------
# Habit simulation tests
# ---------------------------------------------------------------------------

def test_habit_baseline_simulation():
    results = run_habit_simulation(
        user_id=1,
        current_completion_rate=60,
        exercise_frequency=3,
        avg_steps=7000,
        avg_sleep_hours=7,
        horizon_months=6,
    )
    assert len(results) >= 4
    baseline = next(s for s in results if s.is_baseline)
    assert "projected_fitness_score" in baseline.output_metrics
    assert len(baseline.time_series) == 6


def test_habit_improved_exercise():
    results = run_habit_simulation(
        user_id=1,
        current_completion_rate=60,
        exercise_frequency=3,
        avg_steps=7000,
        avg_sleep_hours=7,
        horizon_months=6,
    )
    baseline = next(s for s in results if s.is_baseline)
    improved = [s for s in results if s.input_params["exercise_frequency"] > 3]
    assert len(improved) > 0
    assert improved[0].output_metrics["projected_fitness_score"] >= baseline.output_metrics["projected_fitness_score"]


def test_fitness_score_computation():
    score = _compute_fitness_score(exercise_frequency=5, avg_steps=8000, avg_sleep=7.5, completion_rate=70)
    assert 0 <= score <= 100
    low_score = _compute_fitness_score(0, 0, 0, 0)
    high_score = _compute_fitness_score(7, 15000, 8, 100)
    assert high_score > low_score


# ---------------------------------------------------------------------------
# Scenario comparison / scoring tests
# ---------------------------------------------------------------------------

def test_compare_scenarios_finance():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    scored = compare_scenarios(scenarios, "finance")
    assert all(s.score > 0 for s in scored)
    assert scored[0].score >= scored[-1].score  # sorted descending
    assert scored[0].score_breakdown


def test_compare_scenarios_study():
    scenarios = run_study_simulation(
        user_id=1,
        current_hours=3.0,
        current_score=65.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    scored = compare_scenarios(scenarios, "study")
    assert all(s.score > 0 for s in scored)


def test_compare_scenarios_habits():
    scenarios = run_habit_simulation(
        user_id=1,
        current_completion_rate=60,
        exercise_frequency=3,
        avg_steps=7000,
        avg_sleep_hours=7,
        horizon_months=6,
    )
    scored = compare_scenarios(scenarios, "habits")
    assert all(s.score > 0 for s in scored)


def test_compare_empty_scenarios():
    scored = compare_scenarios([], "finance")
    assert scored == []


def test_comparison_table():
    scenarios = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    scored = compare_scenarios(scenarios, "finance")
    table = get_comparison_table(scored, "finance")
    assert len(table) == len(scenarios)
    assert "Scenario" in table[0]
    assert "Score" in table[0]


# ---------------------------------------------------------------------------
# Full simulation dispatcher test
# ---------------------------------------------------------------------------

def test_run_simulation_finance():
    request = SimulationRequest(user_id=1, domain="finance", horizon_months=12)
    user_data = {
        "financial": {
            "monthly_income": 50000,
            "monthly_expenses": 35000,
            "monthly_savings": 15000,
            "total_savings": 100000,
        },
        "goals": [{"goal_name": "Emergency Fund", "target_amount": 500000, "current_progress": 100000}],
    }
    result = run_simulation(request, user_data)
    assert "scenarios" in result
    assert "recommendation" in result
    assert len(result["scenarios"]) >= 4
    assert result["recommendation"] is not None


def test_run_simulation_study():
    request = SimulationRequest(user_id=1, domain="study", horizon_months=6)
    user_data = {
        "study": {
            "avg_hours_per_day": 3.0,
            "avg_performance_score": 65.0,
            "subjects": ["Maths"],
        },
    }
    result = run_simulation(request, user_data)
    assert len(result["scenarios"]) >= 4


def test_run_simulation_habits():
    request = SimulationRequest(user_id=1, domain="habits", horizon_months=6)
    user_data = {
        "habits": {
            "avg_completion_rate": 60,
            "exercise_frequency": 3,
            "avg_steps": 7000,
            "avg_sleep_hours": 7,
        },
    }
    result = run_simulation(request, user_data)
    assert len(result["scenarios"]) >= 4


def test_run_simulation_invalid_domain():
    request = SimulationRequest(user_id=1, domain="invalid", horizon_months=6)
    try:
        run_simulation(request, {})
        assert False, "Should raise ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------

def test_financial_zero_income():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=0,
        monthly_expenses=10000,
        current_savings=50000,
        monthly_saving=0,
        horizon_months=6,
    )
    assert len(results) >= 4
    baseline = next(s for s in results if s.is_baseline)
    assert baseline.output_metrics["sustainable"] is False


def test_financial_zero_expenses():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=0,
        current_savings=100000,
        monthly_saving=50000,
        horizon_months=12,
    )
    baseline = next(s for s in results if s.is_baseline)
    assert baseline.output_metrics["final_balance"] == 100000 + 50000 * 12
    assert baseline.output_metrics["sustainable"] is True


def test_study_zero_hours():
    results = run_study_simulation(
        user_id=1,
        current_hours=0,
        current_score=50.0,
        subjects=["Maths"],
        horizon_months=6,
    )
    assert len(results) >= 4


def test_habit_zero_exercise():
    results = run_habit_simulation(
        user_id=1,
        current_completion_rate=0,
        exercise_frequency=0,
        avg_steps=0,
        avg_sleep_hours=0,
        horizon_months=6,
    )
    assert len(results) >= 4
    baseline = next(s for s in results if s.is_baseline)
    assert baseline.output_metrics["projected_fitness_score"] == 0


# ---------------------------------------------------------------------------
# Simulation output structure tests
# ---------------------------------------------------------------------------

def test_scenario_result_structure():
    results = run_financial_simulation(
        user_id=1,
        monthly_income=50000,
        monthly_expenses=35000,
        current_savings=100000,
        monthly_saving=15000,
        horizon_months=12,
    )
    for s in results:
        assert hasattr(s, "name")
        assert hasattr(s, "description")
        assert hasattr(s, "is_baseline")
        assert hasattr(s, "input_params")
        assert hasattr(s, "output_metrics")
        assert hasattr(s, "time_series")
        assert hasattr(s, "score")
        assert isinstance(s.input_params, dict)
        assert isinstance(s.output_metrics, dict)
        assert isinstance(s.time_series, list)
