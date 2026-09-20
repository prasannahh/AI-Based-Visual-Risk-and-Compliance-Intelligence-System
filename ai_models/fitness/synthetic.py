"""
ai_models/fitness/synthetic.py
Realistic synthetic data generators for the fitness domain.

Synthetic data lets the training + evaluation pipeline run out of the box.
Swap these functions for consented, real user records before production use.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def fitness_score_formula(exercise_frequency, daily_steps, sleep_hours, calories_burned, bmi) -> np.ndarray:
    """Explainable composite score in [0, 100] used to label synthetic rows.

    Weights: exercise 25, steps 25, sleep 20, calories 15, BMI 15.
    """
    exercise_part = np.minimum(np.asarray(exercise_frequency) / 6.0, 1.0) * 25
    steps_part = np.minimum(np.asarray(daily_steps) / 10000.0, 1.0) * 25
    sleep_part = (1 - np.minimum(np.abs(np.asarray(sleep_hours) - 7.5) / 4.0, 1.0)) * 20
    calories_part = np.minimum(np.asarray(calories_burned) / 600.0, 1.0) * 15
    bmi_part = (1 - np.minimum(np.maximum(np.asarray(bmi) - 18.5, 0.0) / 13.0, 1.0)) * 15
    return np.clip(exercise_part + steps_part + sleep_part + calories_part + bmi_part, 0, 100)


def synthetic_fitness_score_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Synthetic rows of fitness inputs with a labelled 0-100 score."""
    rng = np.random.default_rng(seed)
    exercise_frequency = rng.integers(0, 8, rows)
    daily_steps = rng.integers(0, 22000, rows)
    sleep_hours = rng.normal(7.0, 1.5, rows).clip(3, 11)
    calories_burned = rng.normal(350, 220, rows).clip(0, 1600)
    bmi = rng.normal(26, 5, rows).clip(16, 42)
    score = fitness_score_formula(exercise_frequency, daily_steps, sleep_hours, calories_burned, bmi)
    score = np.clip(score + rng.normal(0, 2.5, rows), 0, 100).round(1)
    return pd.DataFrame(
        {
            "exercise_frequency": exercise_frequency,
            "daily_steps": daily_steps,
            "sleep_hours": sleep_hours.round(1),
            "calories_burned": calories_burned.round(0),
            "bmi": bmi.round(1),
            "fitness_score": score,
        }
    )


def synthetic_goal_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Synthetic rows for the goal-achievement binary classifier.

    The outcome label is derived from current progress, effort level and the
    time available, so it can be learned by a classifier.
    """
    rng = np.random.default_rng(seed)
    current_score = rng.uniform(20, 90, rows)
    goal_score = np.clip(current_score + rng.uniform(10, 60, rows), 0, 100)
    days_to_goal = rng.integers(7, 180, rows)
    exercise_frequency = rng.integers(0, 8, rows)
    daily_steps = rng.integers(0, 22000, rows)
    sleep_hours = rng.normal(7.0, 1.5, rows).clip(3, 11)

    progress_ratio = current_score / goal_score
    effort = ((exercise_frequency / 7.0) + np.minimum(daily_steps / 10000.0, 1.0)) / 2.0
    days_factor = np.minimum(days_to_goal / 120.0, 1.0)
    logit = 3.0 * (progress_ratio - 0.6) + 2.0 * effort - 0.8 + 1.5 * days_factor
    prob = 1 / (1 + np.exp(-logit))
    reached = (prob + rng.normal(0, 0.06, rows) > 0.5).astype(int)
    return pd.DataFrame(
        {
            "current_score": current_score.round(1),
            "goal_score": goal_score.round(1),
            "days_to_goal": days_to_goal,
            "exercise_frequency": exercise_frequency,
            "daily_steps": daily_steps,
            "sleep_hours": sleep_hours.round(1),
            "goal_reached": reached,
        }
    )
