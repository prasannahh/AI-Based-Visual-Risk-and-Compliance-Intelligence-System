"""
ai_models/fitness/preprocess.py
Pipeline builders for the fitness domain (all numeric features).
"""

from __future__ import annotations

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _numeric_pipeline(algorithm: object) -> Pipeline:
    return Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", algorithm)]
    )


def build_fitness_score_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for predicting the 0-100 fitness score."""
    return _numeric_pipeline(algorithm)


def build_goal_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for binary goal-achievement classification."""
    return _numeric_pipeline(algorithm)
