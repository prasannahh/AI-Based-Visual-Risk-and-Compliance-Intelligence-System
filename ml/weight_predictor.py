"""
ml/weight_predictor.py
-----------------------
A scikit-learn RandomForestRegressor that predicts *how much weight (kg) a
person will gain or lose* over a given time horizon, based on their energy
balance and lifestyle habits.

Because there is no proprietary dataset for this student project, the model
is trained on a large synthetic dataset generated from the well-established
"~7700 kcal per kg of body fat" energy-balance rule, with realistic noise
added so the model learns a smooth, generalizable relationship instead of
just memorizing the formula. This is a standard technique for prototyping
ML systems before real user data is available -- and is exactly why the
Digital Twin keeps improving as real daily logs accumulate (see
train_models.py -> retrain_with_real_data()).
"""

import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "weight_predictor.pkl")

FEATURE_NAMES = [
    "current_weight_kg",
    "height_cm",
    "age",
    "is_female",
    "avg_daily_calorie_balance",  # consumed - TDEE (positive = surplus)
    "avg_sleep_hours",
    "avg_steps",
    "horizon_days",
]


def _generate_synthetic_dataset(n_samples: int = 8000, seed: int = 42):
    rng = np.random.default_rng(seed)

    weight = rng.uniform(45, 130, n_samples)
    height = rng.uniform(150, 200, n_samples)
    age = rng.integers(16, 70, n_samples)
    is_female = rng.integers(0, 2, n_samples)
    calorie_balance = rng.uniform(-1000, 1000, n_samples)  # kcal/day surplus or deficit
    sleep = rng.uniform(4, 9, n_samples)
    steps = rng.integers(500, 18000, n_samples)
    horizon = rng.integers(7, 180, n_samples)

    # Core physics: ~7700 kcal deficit/surplus per kg of body weight.
    base_change = (calorie_balance * horizon) / 7700.0

    # Sleep deprivation slows fat loss / promotes gain (metabolic + hormonal effect).
    sleep_penalty = np.where(sleep < 6, (6 - sleep) * 0.01 * horizon, 0)

    # High daily steps slightly improve results beyond raw calorie burn
    # (captured loosely in calorie_balance already, small extra effect here).
    activity_bonus = np.where(steps > 10000, -0.003 * horizon, 0)

    noise = rng.normal(0, 0.6, n_samples)  # individual variability

    weight_change = base_change + sleep_penalty + activity_bonus + noise

    X = np.column_stack([weight, height, age, is_female, calorie_balance, sleep, steps, horizon])
    y = weight_change
    return X, y


def train_and_save():
    X, y = _generate_synthetic_dataset()
    model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X, y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_and_save()
    return joblib.load(MODEL_PATH)


def predict_weight_change(
    current_weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    avg_daily_calorie_balance: float,
    avg_sleep_hours: float,
    avg_steps: float,
    horizon_days: int,
) -> float:
    """Returns predicted weight CHANGE in kg (can be negative)."""
    model = load_model()
    is_female = 1 if gender and gender.lower().startswith("f") else 0
    X = np.array([[
        current_weight_kg, height_cm, age, is_female,
        avg_daily_calorie_balance, avg_sleep_hours, avg_steps, horizon_days
    ]])
    return round(float(model.predict(X)[0]), 2)
