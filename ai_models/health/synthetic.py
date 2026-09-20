"""
ai_models/health/synthetic.py
Realistic synthetic data generators for the health domain.

These datasets exist so the training + evaluation pipeline works out of the
box. Replace `synthetic_weight_data`, `synthetic_calorie_data` and
`synthetic_risk_data` with consented, real-world records before any
production use (see README, "Replacing synthetic data").
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai_models.common import feature_engineering as fe
from ai_models.health import model as hmodel


def synthetic_weight_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Synthetic profile + intake rows with a physically plausible target.

    next_weight = weight + (calories - maintenance) / 7700 (kcal per kg of
    body mass), plus small measurement noise.
    """
    rng = np.random.default_rng(seed)
    gender = rng.choice(["female", "male"], rows)
    age = rng.integers(18, 71, rows)
    height = rng.normal(170, 10, rows).clip(145, 205)
    weight = rng.normal(72, 15, rows).clip(42, 150)
    activity = rng.choice(["sedentary", "light", "moderate", "active", "very_active"], rows)
    calories = rng.normal(2200, 500, rows).clip(1000, 4500)
    maintenance = 10 * weight + 6.25 * height - 5 * age + np.where(gender == "male", 5, -161)
    maintenance += pd.Series(activity).map(fe.ACTIVITY_BURN).to_numpy()
    next_weight = weight + (calories - maintenance) / 7700 + rng.normal(0, 0.08, rows)
    return pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height,
            "current_weight_kg": weight,
            "activity_level": activity,
            "daily_calories": calories,
            "next_weight_kg": next_weight,
        }
    )


def synthetic_calorie_data(rows: int = 3000, seed: int = 42) -> pd.DataFrame:
    """Synthetic profiles whose daily calorie target follows Mifflin-St Jeor
    scaled by the activity multiplier, with realistic noise."""
    rng = np.random.default_rng(seed)
    gender = rng.choice(["female", "male"], rows)
    age = rng.integers(18, 71, rows)
    height = rng.normal(170, 10, rows).clip(145, 205)
    weight = rng.normal(72, 15, rows).clip(42, 150)
    activity = rng.choice(["sedentary", "light", "moderate", "active", "very_active"], rows)
    base = fe.mifflin_st_jeor(age.astype(int), gender, weight, height)
    factor = pd.Series(activity).map(fe.ACTIVITY_FACTORS).to_numpy()
    calories = (base * factor + rng.normal(0, 60, rows)).clip(1200, 5000)
    return pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height,
            "weight_kg": weight,
            "activity_level": activity,
            "daily_calories": calories.round(0),
        }
    )


def _risk_probabilities(rng: np.random.Generator, age, bmi_values, activity, calories, exercise_frequency) -> dict[str, np.ndarray]:
    """Sigmoid-style risk probabilities used to label the synthetic data."""
    sedentary = np.array([1 if a == "sedentary" else 0 for a in activity])
    inactive = np.array([1 if a in ("sedentary", "light") else 0 for a in activity])

    def sigmoid(x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-x))

    p_obesity = sigmoid((bmi_values - 26) / 4 - 0.3 * np.maximum(0, 8 - np.minimum(age / 10, 8)))
    p_diabetes = sigmoid((age - 48) / 12 + 0.15 * (bmi_values - 26) - 0.5 * np.maximum(0, exercise_frequency - 2))
    p_hypertension = sigmoid((age - 50) / 11 + 0.12 * (bmi_values - 25) + 0.3 * sedentary - 0.0015 * (calories - 2200) * inactive)
    return {"obesity": p_obesity, "diabetes": p_diabetes, "hypertension": p_hypertension}


def synthetic_risk_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Synthetic records with binary targets for obesity / diabetes /
    hypertension, generated from realistic risk-driving rules."""
    rng = np.random.default_rng(seed)
    gender = rng.choice(["female", "male"], rows)
    age = rng.integers(18, 80, rows)
    height = rng.normal(170, 10, rows).clip(145, 205)
    weight = rng.normal(72, 16, rows).clip(42, 160)
    activity = rng.choice(["sedentary", "light", "moderate", "active", "very_active"], rows, p=[0.3, 0.25, 0.2, 0.15, 0.1])
    calories = rng.normal(2200, 500, rows).clip(1000, 4500)
    exercise_frequency = rng.integers(0, 8, rows)
    bmi_values = fe.bmi(weight, height)

    probs = _risk_probabilities(rng, age, bmi_values, activity, calories, exercise_frequency)
    noise = rng.normal(0, 0.05, rows)
    return pd.DataFrame(
        {
            "age": age,
            "gender": gender,
            "height_cm": height,
            "weight_kg": weight,
            "activity_level": activity,
            "daily_calories": calories,
            "exercise_frequency": exercise_frequency,
            "risk_obesity": (probs["obesity"] + noise > 0.5).astype(int),
            "risk_diabetes": (probs["diabetes"] + noise > 0.5).astype(int),
            "risk_hypertension": (probs["hypertension"] + noise > 0.5).astype(int),
        }
    )
