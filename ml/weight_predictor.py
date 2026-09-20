"""Weight forecasting wrapper around the trained scikit-learn pipeline."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


class WeightPredictor:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    @classmethod
    def load(cls, model_path: Path) -> "WeightPredictor":
        return cls(joblib.load(model_path))

    def forecast(self, *, age: int, gender: str, height_cm: float, current_weight_kg: float, activity_level: str, daily_calories: int, days: int) -> pd.DataFrame:
        rows = []
        weight = float(current_weight_kg)
        for day in range(1, days + 1):
            frame = pd.DataFrame([{"age": age, "gender": gender, "height_cm": height_cm, "current_weight_kg": weight, "activity_level": activity_level, "daily_calories": daily_calories}])
            weight = max(25.0, float(self.pipeline.predict(frame)[0]))
            rows.append({"day": day, "predicted_weight_kg": round(weight, 2)})
        return pd.DataFrame(rows)
