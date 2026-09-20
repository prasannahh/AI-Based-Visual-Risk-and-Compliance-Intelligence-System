"""
ai_models/health/model.py
Model registry for the health domain: feature lists, targets and candidate
algorithms (defined centrally in ai_models.common.algorithms).
"""

from __future__ import annotations

from ai_models.common.algorithms import candidate_classifiers, candidate_regressors

WEIGHT_FEATURES = ["age", "gender", "height_cm", "current_weight_kg", "activity_level", "daily_calories"]
WEIGHT_TARGET = "next_weight_kg"

CALORIE_FEATURES = ["age", "gender", "height_cm", "weight_kg", "activity_level"]
CALORIE_TARGET = "daily_calories"

RISK_FEATURES = ["age", "gender", "height_cm", "weight_kg", "activity_level", "daily_calories", "exercise_frequency"]

RISK_LABELS = {"risk_obesity": "Obesity", "risk_diabetes": "Diabetes", "risk_hypertension": "Hypertension"}
