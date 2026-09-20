"""Baseline model training and hold-out validation."""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def synthetic_training_data(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Create demo-only data with plausible weight-change relationships."""
    rng = np.random.default_rng(seed)
    gender = rng.choice(["female", "male"], rows)
    age = rng.integers(18, 71, rows)
    height = rng.normal(170, 10, rows).clip(145, 205)
    weight = rng.normal(72, 15, rows).clip(42, 150)
    activity = rng.choice(["sedentary", "light", "moderate", "active", "very_active"], rows)
    calories = rng.normal(2200, 500, rows).clip(1000, 4500)
    activity_burn = pd.Series(activity).map({"sedentary": 0, "light": 150, "moderate": 300, "active": 500, "very_active": 700}).to_numpy()
    maintenance = 10 * weight + 6.25 * height - 5 * age + np.where(gender == "male", 5, -161) + activity_burn
    next_weight = weight + (calories - maintenance) / 7700 + rng.normal(0, 0.08, rows)
    return pd.DataFrame({"age": age, "gender": gender, "height_cm": height, "current_weight_kg": weight, "activity_level": activity, "daily_calories": calories, "next_weight_kg": next_weight})


def train_weight_model(model_path: Path) -> dict[str, float]:
    data = synthetic_training_data()
    features = ["age", "gender", "height_cm", "current_weight_kg", "activity_level", "daily_calories"]
    x_train, x_test, y_train, y_test = train_test_split(data[features], data["next_weight_kg"], test_size=0.2, random_state=42)
    preprocess = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), ["gender", "activity_level"])], remainder="passthrough")
    pipeline = Pipeline([("preprocess", preprocess), ("model", RandomForestRegressor(n_estimators=200, min_samples_leaf=3, random_state=42, n_jobs=-1))])
    pipeline.fit(x_train, y_train)
    prediction = pipeline.predict(x_test)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    return {"mae": float(mean_absolute_error(y_test, prediction)), "r2": float(r2_score(y_test, prediction))}
