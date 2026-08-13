"""Calorie-expenditure model trained from the Hugging Face dataset."""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd


class CaloriePredictor:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    @classmethod
    def load(cls, model_path: Path) -> "CaloriePredictor":
        return cls(joblib.load(model_path))

    def predict(self, *, age: int, gender: str, height_cm: float, weight_kg: float, duration_minutes: float, heart_rate: float, body_temp_c: float) -> float:
        row = pd.DataFrame([{"Gender": gender, "Age": age, "Height": height_cm, "Weight": weight_kg, "Duration": duration_minutes, "Heart_Rate": heart_rate, "Body_Temp": body_temp_c}])
        return max(0.0, float(self.pipeline.predict(row)[0]))
