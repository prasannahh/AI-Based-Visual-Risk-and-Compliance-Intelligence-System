"""
ai_models/fitness/model.py
Model registry for the fitness domain: feature lists, targets and config.
Candidate algorithms live centrally in ai_models.common.algorithms.
"""

from __future__ import annotations

FITNESS_SCORE_FEATURES = ["exercise_frequency", "daily_steps", "sleep_hours", "calories_burned", "bmi"]
FITNESS_SCORE_TARGET = "fitness_score"

GOAL_FEATURES = ["current_score", "goal_score", "days_to_goal", "exercise_frequency", "daily_steps", "sleep_hours"]
GOAL_TARGET = "goal_reached"

WORKOUT_PLANS = {
    "beginner": {
        "duration_minutes": 25,
        "calories_target": 200,
        "exercises": ["Walking / brisk walking", "Bodyweight squats", "Wall push-ups", "Light stretching"],
    },
    "intermediate": {
        "duration_minutes": 40,
        "calories_target": 350,
        "exercises": ["Jogging", "Push-ups", "Lunges", "Plank hold"],
    },
    "advanced": {
        "duration_minutes": 55,
        "calories_target": 500,
        "exercises": ["HIIT circuit", "Burpees", "Sprint intervals", "Kettlebell swings"],
    },
}
