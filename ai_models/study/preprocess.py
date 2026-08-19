"""
ai_models/study/preprocess.py
Pipeline builder for the study domain (one categorical + four numeric cols).
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_COLS = ["hours_logged", "days_to_exam", "study_consistency", "prior_score"]


def build_performance_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for predicting an academic performance score (0-100)."""
    transformer = ColumnTransformer(
        [
            ("subject", OneHotEncoder(handle_unknown="ignore"), ["subject"]),
            ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), NUMERIC_COLS),
        ]
    )
    return Pipeline([("preprocess", transformer), ("model", algorithm)])
