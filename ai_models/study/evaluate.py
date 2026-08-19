"""
ai_models/study/evaluate.py
Hold-out evaluation and model comparison for the study domain.
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from ai_models.common.algorithms import candidate_regressors
from ai_models.common.metrics import compare_regressors
from ai_models.common.utils import load_model
from ai_models.study import model as smodel
from ai_models.study import preprocess as sprep
from ai_models.study import synthetic as ssynth


def evaluate_performance_model() -> pd.DataFrame:
    """Comparison table of candidate regressors for academic performance."""
    data = ssynth.synthetic_performance_data()
    x_train, x_test, y_train, y_test = train_test_split(data[smodel.PERFORMANCE_FEATURES], data[smodel.PERFORMANCE_TARGET], test_size=0.2, random_state=42)
    estimators = {n: sprep.build_performance_pipeline(est) for n, est in candidate_regressors().items()}
    return compare_regressors(estimators, x_train, y_train, x_test, y_test)


def saved_model_metrics() -> dict[str, dict]:
    """Metrics recorded when the currently persisted model was trained."""
    _, meta = load_model("study", "performance_predictor")
    return {"performance_predictor": meta} if meta else {}
