"""
ai_models/fitness/predict.py
Prediction and recommendation APIs for the fitness domain: fitness score,
workout plan, weekly activity trend and goal-achievement probability.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai_models.common.utils import get_or_train
from ai_models.fitness import model as fmodel
from ai_models.fitness import train as ftrain

INACTIVE_STEPS = 5000
INACTIVE_MINUTES_WEEKLY = 60


def _score_level(score: float) -> str:
    if score < 40:
        return "beginner"
    if score < 70:
        return "intermediate"
    return "advanced"


def predict_fitness_score(exercise_frequency: int, daily_steps: int, sleep_hours: float, calories_burned: float, bmi: float) -> dict:
    """Predict the 0-100 fitness score and map it to a fitness level.

    Returns:
        {'score', 'level'}.
    """
    model, _ = get_or_train("fitness", "fitness_score_predictor", ftrain.train_fitness_score_model)
    frame = pd.DataFrame(
        [[exercise_frequency, daily_steps, sleep_hours, calories_burned, bmi]],
        columns=fmodel.FITNESS_SCORE_FEATURES,
    )
    score = float(np.clip(model.predict(frame)[0], 0, 100))
    return {"score": round(score, 1), "level": _score_level(score)}


def recommend_workout(score: float, bmi: float, goal: str = "maintain") -> dict:
    """Rule-based workout recommendation engine.

    Args:
        score: Current fitness score (0-100).
        bmi: User BMI.
        goal: 'lose', 'gain' or 'maintain'.

    Returns:
        {'level', 'duration_minutes', 'calories_target', 'exercises', 'notes'}.
    """
    level = _score_level(score)
    plan = dict(fmodel.WORKOUT_PLANS[level])

    if goal == "lose":
        plan["exercises"] = ["Brisk walking", "Jogging", "Cycling", "Bodyweight circuits", "Swimming"]
        plan["duration_minutes"] = plan["duration_minutes"] + 10
    elif goal == "gain":
        plan["exercises"] = ["Strength training", "Push-ups / rows", "Squats & lunges", "Core work"]
        plan["duration_minutes"] = max(plan["duration_minutes"] - 5, 20)

    notes = []
    if bmi >= 30:
        notes.append("Low-impact start recommended: walking, swimming or cycling to protect the joints.")
    if goal == "lose":
        notes.append("Combine this plan with a modest calorie deficit of 300-500 kcal/day.")
    elif goal == "gain":
        notes.append("Pair resistance training with a slight calorie surplus and adequate protein.")

    plan["level"] = level.capitalize()
    plan["notes"] = notes
    return plan


def predict_weekly_activity(activity_df: pd.DataFrame, weeks_ahead: int = 8) -> dict:
    """Forecast weekly activity and flag inactive users.

    Args:
        activity_df: DataFrame with a 'date' column and either 'steps' or
            'exercise_minutes' (or both).
        weeks_ahead: Number of weeks to forecast.

    Returns:
        {'forecast': DataFrame[week, predicted_steps],
         'inactive': bool, 'message': str, 'avg_daily_steps': float}.
    """
    if activity_df.empty or "date" not in activity_df.columns:
        return {"forecast": pd.DataFrame(columns=["week", "predicted_steps"]), "inactive": False, "message": "No activity data yet.", "avg_daily_steps": 0.0}

    df = activity_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    avg_daily_steps = float(df["steps"].mean()) if "steps" in df.columns else 0.0
    inactive = avg_daily_steps < INACTIVE_STEPS
    if "exercise_minutes" in df.columns and not inactive:
        weekly_minutes = df["exercise_minutes"].sum() / max(df["date"].dt.isocalendar().week.nunique(), 1)
        inactive = weekly_minutes < INACTIVE_MINUTES_WEEKLY

    steps_col = "steps" if "steps" in df.columns else "exercise_minutes"
    weekly = df.set_index("date").resample("W")[steps_col].sum().fillna(0).reset_index()
    weeks = np.arange(len(weekly))
    values = weekly[steps_col].to_numpy(dtype=float)
    if len(weeks) >= 2:
        slope, intercept = np.polyfit(weeks, values, 1)
        pred_x = np.arange(len(weekly), len(weekly) + weeks_ahead)
        pred = np.maximum(slope * pred_x + intercept, 0)
    else:
        pred = np.full(weeks_ahead, float(values.mean()) if len(values) else 0.0)

    forecast = pd.DataFrame({"week": [f"Week +{i + 1}" for i in range(weeks_ahead)], "predicted_steps": pred.round(0)})
    message = (
        "Activity is below the recommended baseline — try to reach 5,000+ steps a day."
        if inactive
        else "Activity looks healthy; keep it consistent."
    )
    return {"forecast": forecast, "inactive": inactive, "message": message, "avg_daily_steps": round(avg_daily_steps, 0)}


def predict_goal_achievement(current_score: float, goal_score: float, days_to_goal: int, exercise_frequency: int, daily_steps: int, sleep_hours: float) -> dict:
    """Probability of reaching a fitness goal within the given timeframe.

    Returns:
        {'probability_pct', 'level', 'recommendation'}.
    """
    model, _ = get_or_train("fitness", "goal_achievement", ftrain.train_goal_model)
    frame = pd.DataFrame(
        [[current_score, goal_score, days_to_goal, exercise_frequency, daily_steps, sleep_hours]],
        columns=fmodel.GOAL_FEATURES,
    )
    probability = float(model.predict_proba(frame)[0][1]) * 100
    if probability < 40:
        level, recommendation = "Low", "Your goal looks ambitious for this timeline — raise effort or extend the deadline."
    elif probability < 70:
        level, recommendation = "Moderate", "You're on track. Increase consistency and weekly volume to close the gap."
    else:
        level, recommendation = "High", "You're well positioned. Keep your routine and monitor progress weekly."
    return {"probability_pct": round(probability, 1), "level": level, "recommendation": recommendation}
