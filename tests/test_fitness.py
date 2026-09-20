"""Tests for the fitness AI module."""

import pandas as pd

from ai_models.fitness import evaluate as feval
from ai_models.fitness import predict as fpredict


def test_predict_fitness_score_bounds():
    low = fpredict.predict_fitness_score(0, 0, 3, 0, 35)
    high = fpredict.predict_fitness_score(7, 20000, 8, 1200, 22)
    assert 0 <= low["score"] <= 100
    assert high["score"] > low["score"]
    assert low["level"] in {"beginner", "intermediate", "advanced"}


def test_recommend_workout_structure():
    plan = fpredict.recommend_workout(60, 26, "lose")
    assert set(["level", "duration_minutes", "calories_target", "exercises", "notes"]) <= set(plan)
    assert plan["exercises"]
    assert plan["duration_minutes"] > 0
    assert plan["calories_target"] > 0


def test_recommend_workout_levels():
    beginner = fpredict.recommend_workout(25, 26, "maintain")
    advanced = fpredict.recommend_workout(85, 22, "gain")
    assert beginner["level"] == "Beginner"
    assert advanced["level"] == "Advanced"


def test_predict_weekly_activity_empty():
    result = fpredict.predict_weekly_activity(pd.DataFrame())
    assert result["forecast"].empty
    assert result["inactive"] is False


def test_predict_weekly_activity_forecast():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=21, freq="D"), "steps": [7000] * 21})
    result = fpredict.predict_weekly_activity(df, weeks_ahead=4)
    assert len(result["forecast"]) == 4
    assert (result["forecast"]["predicted_steps"] > 0).all()
    assert result["inactive"] is False


def test_predict_weekly_activity_detects_inactive():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=21, freq="D"), "steps": [2000] * 21})
    result = fpredict.predict_weekly_activity(df, weeks_ahead=2)
    assert result["inactive"] is True


def test_predict_goal_achievement():
    outcome = fpredict.predict_goal_achievement(60, 85, 90, 4, 9000, 7.5)
    assert 0 <= outcome["probability_pct"] <= 100
    assert outcome["level"] in {"Low", "Moderate", "High"}
    assert outcome["recommendation"]


def test_evaluate_fitness_score_table():
    table = feval.evaluate_fitness_score_model()
    assert "model" in table.columns and "best" in table.columns
