"""
ai_models/fitness/evaluate.py
Hold-out evaluation and model comparison for the fitness domain.
"""

from __future__ import annotations

import pandas as pd

from ai_models.common.algorithms import candidate_classifiers, candidate_regressors
from ai_models.common.metrics import compare_classifiers, compare_regressors
from ai_models.common.utils import load_model
from ai_models.fitness import model as fmodel
from ai_models.fitness import preprocess as fprep
from ai_models.fitness import synthetic as fsynth
from sklearn.model_selection import train_test_split


def evaluate_fitness_score_model() -> pd.DataFrame:
    """Comparison table of candidate regressors for the fitness score."""
    data = fsynth.synthetic_fitness_score_data()
    x_train, x_test, y_train, y_test = train_test_split(data[fmodel.FITNESS_SCORE_FEATURES], data[fmodel.FITNESS_SCORE_TARGET], test_size=0.2, random_state=42)
    estimators = {n: fprep.build_fitness_score_pipeline(est) for n, est in candidate_regressors().items()}
    return compare_regressors(estimators, x_train, y_train, x_test, y_test)


def evaluate_goal_model() -> pd.DataFrame:
    """Comparison table of candidate classifiers for goal achievement."""
    data = fsynth.synthetic_goal_data()
    x_train, x_test, y_train, y_test = train_test_split(data[fmodel.GOAL_FEATURES], data[fmodel.GOAL_TARGET], test_size=0.2, random_state=42)
    estimators = {n: fprep.build_goal_pipeline(est) for n, est in candidate_classifiers().items()}
    return compare_classifiers(estimators, x_train, y_train, x_test, y_test)


def saved_model_metrics() -> dict[str, dict]:
    """Metrics recorded when the currently persisted models were trained."""
    out = {}
    for name in ["fitness_score_predictor", "goal_achievement"]:
        _, meta = load_model("fitness", name)
        if meta:
            out[name] = meta
    return out
