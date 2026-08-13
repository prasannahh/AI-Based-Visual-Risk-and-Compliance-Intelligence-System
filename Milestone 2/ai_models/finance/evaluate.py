"""
ai_models/finance/evaluate.py
Hold-out evaluation and model comparison for the finance domain.
"""

from __future__ import annotations

import pandas as pd

from ai_models.common.metrics import compare_classifiers
from ai_models.common.utils import load_model
from ai_models.finance import model as fmodel
from ai_models.finance import preprocess as fprep
from ai_models.finance import synthetic as fsynth
from ai_models.finance import train as ftrain
from sklearn.model_selection import train_test_split


def evaluate_expense_classifier() -> pd.DataFrame:
    """Comparison table of candidate classifiers for expense classification."""
    data = fsynth.synthetic_expense_data()
    x_train, x_test, y_train, y_test = train_test_split(data[fmodel.EXPENSE_FEATURES], data[fmodel.EXPENSE_TARGET], test_size=0.2, random_state=42)
    estimators = {n: fprep.build_expense_pipeline(est) for n, est in ftrain.candidate_expense_classifiers().items()}
    return compare_classifiers(estimators, x_train, y_train, x_test, y_test)


def saved_model_metrics() -> dict[str, dict]:
    """Metrics recorded when the currently persisted model was trained."""
    _, meta = load_model("finance", "expense_classifier")
    return {"expense_classifier": meta} if meta else {}
