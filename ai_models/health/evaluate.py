"""
ai_models/health/evaluate.py
Hold-out evaluation and model comparison for the health domain. Useful for
command-line validation and for the "Model training" UI panels.
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from ai_models.common.metrics import best_model, compare_classifiers, compare_regressors
from ai_models.common.utils import load_model
from ai_models.health import model as hmodel
from ai_models.health import preprocess as hprep
from ai_models.health import synthetic as hsynth


def _pipeline_estimators(build_pipeline, algorithms: dict) -> dict:
    """Wrap each candidate algorithm in its domain preprocessing pipeline."""
    return {name: build_pipeline(est) for name, est in algorithms.items()}


def evaluate_weight_model() -> pd.DataFrame:
    """Comparison table of all candidate regressors for next-weight."""
    data = hsynth.synthetic_weight_data()
    x_train, x_test, y_train, y_test = train_test_split(data[hmodel.WEIGHT_FEATURES], data[hmodel.WEIGHT_TARGET], test_size=0.2, random_state=42)
    estimators = _pipeline_estimators(hprep.build_weight_pipeline, hmodel.candidate_regressors())
    return compare_regressors(estimators, x_train, y_train, x_test, y_test)


def evaluate_calorie_model() -> pd.DataFrame:
    """Comparison table of all candidate regressors for daily calories."""
    data = hsynth.synthetic_calorie_data()
    x_train, x_test, y_train, y_test = train_test_split(data[hmodel.CALORIE_FEATURES], data[hmodel.CALORIE_TARGET], test_size=0.2, random_state=42)
    estimators = _pipeline_estimators(hprep.build_calorie_pipeline, hmodel.candidate_regressors())
    return compare_regressors(estimators, x_train, y_train, x_test, y_test)


def evaluate_risk_models() -> dict[str, pd.DataFrame]:
    """Comparison table of all candidate classifiers for each risk label."""
    data = hsynth.synthetic_risk_data()
    tables = {}
    for label in hmodel.RISK_LABELS:
        x_train, x_test, y_train, y_test = train_test_split(data[hmodel.RISK_FEATURES], data[label], test_size=0.2, random_state=42)
        estimators = _pipeline_estimators(hprep.build_risk_pipeline, hmodel.candidate_classifiers())
        tables[label] = compare_classifiers(estimators, x_train, y_train, x_test, y_test)
    return tables


def saved_model_metrics() -> dict[str, dict]:
    """Metrics recorded when the currently persisted models were trained."""
    out = {}
    for name in ["weight_predictor", "calorie_predictor", *hmodel.RISK_LABELS]:
        _, meta = load_model("health", name)
        if meta:
            out[name] = meta
    return out
