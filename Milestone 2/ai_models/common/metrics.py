"""
ai_models/common/metrics.py
Evaluation metrics for regression and classification, plus helpers that
compare several algorithms and rank them, so the best performing model can
be selected automatically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
    r2_score,
)
from sklearn.model_selection import cross_val_score


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """MAE, MSE, RMSE and R² for a regression task."""
    mse = mean_squared_error(y_true, y_pred)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def classification_metrics(y_true, y_pred, y_proba: np.ndarray | None = None, positive: int = 1) -> dict[str, float]:
    """Accuracy, precision, recall, F1 and (optionally) ROC AUC.

    Binary and multiclass targets are both supported; multiclass uses
    macro-averaged precision/recall/F1 and the one-vs-rest ROC AUC.
    """
    classes = np.unique(np.asarray(y_true))
    average = "binary" if len(classes) <= 2 else "macro"
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0, pos_label=positive)),
        "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0, pos_label=positive)),
        "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0, pos_label=positive)),
    }
    if y_proba is not None:
        try:
            if len(classes) <= 2:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1] if y_proba.ndim > 1 else y_proba))
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr"))
        except ValueError:
            metrics["roc_auc"] = 0.0
    return metrics


def compare_regressors(estimators: dict[str, object], X_train, y_train, X_test, y_test, cv: int = 5) -> pd.DataFrame:
    """Train and cross-validate several regressors, returning a ranked table.

    Args:
        estimators: Mapping of {name: unfitted sklearn estimator}.
        X_train/y_train: Training data.
        X_test/y_test: Hold-out data used for the final metrics.
        cv: Number of cross-validation folds.

    Returns:
        Sorted DataFrame of per-model metrics with a 'best' flag.
    """
    rows = []
    for name, model in estimators.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        cv_rmse = cross_val_score(model, X_train, y_train, cv=cv, scoring="neg_mean_squared_error")
        metrics = regression_metrics(y_test, pred)
        metrics["model"] = name
        metrics["cv_rmse"] = float(np.sqrt(-cv_rmse.mean()))
        rows.append(metrics)
    results = pd.DataFrame(rows).sort_values("rmse")
    best = results["model"].iloc[0]
    results["best"] = results["model"] == best
    return results


def compare_classifiers(estimators: dict[str, object], X_train, y_train, X_test, y_test, cv: int = 5) -> pd.DataFrame:
    """Train and cross-validate several classifiers, returning a ranked table.

    Binary classification is assumed; probability columns are selected
    automatically for the ROC AUC computation.

    Args:
        estimators: Mapping of {name: unfitted sklearn classifier}.
        X_train/y_train: Training data.
        X_test/y_test: Hold-out data used for the final metrics.
        cv: Number of cross-validation folds.

    Returns:
        Sorted DataFrame of per-model metrics with a 'best' flag.
    """
    rows = []
    for name, model in estimators.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
        cv_f1 = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_macro", error_score="raise")
        metrics = classification_metrics(y_test, pred, proba)
        metrics["model"] = name
        metrics["cv_f1"] = float(cv_f1.mean())
        rows.append(metrics)
    results = pd.DataFrame(rows).sort_values("f1", ascending=False)
    best = results["model"].iloc[0]
    results["best"] = results["model"] == best
    return results


def best_model(results: pd.DataFrame) -> str:
    """Name of the top-ranked model from a comparison table."""
    return str(results["model"].iloc[0])
