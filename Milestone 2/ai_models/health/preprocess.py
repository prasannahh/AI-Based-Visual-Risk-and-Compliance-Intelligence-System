"""
ai_models/health/preprocess.py
Feature engineering and sklearn pipeline builders for the health domain.
All pipelines accept a raw feature dataframe and produce model-ready input.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL = ["gender", "activity_level"]

WEIGHT_NUMERIC = ["age", "height_cm", "current_weight_kg", "daily_calories"]
CALORIE_NUMERIC = ["age", "height_cm", "weight_kg"]
RISK_NUMERIC = ["age", "height_cm", "weight_kg", "daily_calories", "exercise_frequency"]


def _column_transformer(numeric_cols: list[str]) -> ColumnTransformer:
    """One-hot encode categoricals and standardise numerics together."""
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            (
                "num",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric_cols,
            ),
        ]
    )


def build_weight_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for predicting next-period weight from profile + intake."""
    return Pipeline([("preprocess", _column_transformer(WEIGHT_NUMERIC)), ("model", algorithm)])


def build_calorie_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for predicting daily calorie requirement."""
    return Pipeline([("preprocess", _column_transformer(CALORIE_NUMERIC)), ("model", algorithm)])


def build_risk_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for binary health-risk classification."""
    return Pipeline([("preprocess", _column_transformer(RISK_NUMERIC)), ("model", algorithm)])
