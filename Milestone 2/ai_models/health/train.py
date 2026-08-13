"""
ai_models/health/train.py
Training entry points for the health domain. Each function generates a
dataset, compares every candidate algorithm on a hold-out split, trains the
best-performing pipeline and persists it with a version tag.
"""

from __future__ import annotations

from ai_models.common.algorithms import candidate_classifiers, candidate_regressors
from ai_models.common.training import train_and_persist
from ai_models.health import model as hmodel
from ai_models.health import preprocess as hprep
from ai_models.health import synthetic as hsynth


def train_weight_model() -> dict:
    """Train and persist the best next-weight regressor."""
    data = hsynth.synthetic_weight_data()
    return train_and_persist(
        "health", "weight_predictor", hmodel.WEIGHT_FEATURES, hmodel.WEIGHT_TARGET,
        data, hprep.build_weight_pipeline, candidate_regressors(), display_name="Weight Prediction",
    )


def train_calorie_model() -> dict:
    """Train and persist the best daily-calorie regressor."""
    data = hsynth.synthetic_calorie_data()
    return train_and_persist(
        "health", "calorie_predictor", hmodel.CALORIE_FEATURES, hmodel.CALORIE_TARGET,
        data, hprep.build_calorie_pipeline, candidate_regressors(), display_name="Daily Calorie Prediction",
    )


def train_risk_models() -> dict:
    """Train and persist the three binary health-risk classifiers.

    Returns:
        Mapping of model name -> training metadata.
    """
    data = hsynth.synthetic_risk_data()
    summary = {}
    for label, display in hmodel.RISK_LABELS.items():
        summary[label] = train_and_persist(
            "health", label, hmodel.RISK_FEATURES, label,
            data, hprep.build_risk_pipeline, candidate_classifiers(),
            task="classification", display_name=f"{display} Risk",
        )
    return summary


def train_all() -> dict:
    """Train every health model and return a combined summary."""
    return {
        "weight_predictor": train_weight_model(),
        "calorie_predictor": train_calorie_model(),
        "risk_models": train_risk_models(),
    }
