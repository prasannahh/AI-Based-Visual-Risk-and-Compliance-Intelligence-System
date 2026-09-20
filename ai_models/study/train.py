"""
ai_models/study/train.py
Training entry points for the study domain.
"""

from __future__ import annotations

from ai_models.common.algorithms import candidate_regressors
from ai_models.common.training import train_and_persist
from ai_models.study import model as smodel
from ai_models.study import preprocess as sprep
from ai_models.study import synthetic as ssynth


def train_performance_model() -> dict:
    """Train and persist the best academic-performance regressor."""
    data = ssynth.synthetic_performance_data()
    return train_and_persist(
        "study", "performance_predictor", smodel.PERFORMANCE_FEATURES, smodel.PERFORMANCE_TARGET,
        data, sprep.build_performance_pipeline, candidate_regressors(), display_name="Academic Performance Prediction",
    )


def train_all() -> dict:
    """Train every study model and return a summary."""
    return {"performance_predictor": train_performance_model()}
