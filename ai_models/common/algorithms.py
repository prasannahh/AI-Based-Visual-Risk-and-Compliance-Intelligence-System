"""
ai_models/common/algorithms.py
Shared candidate algorithm factories used by the model-comparison step in
every domain. XGBoost is included when available and degrades gracefully.
"""

from __future__ import annotations

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVR

try:  # XGBoost is optional; the system degrades gracefully if unavailable.
    from xgboost import XGBClassifier, XGBRegressor

    _XGB = True
except Exception:  # pragma: no cover - only when xgboost is missing.
    _XGB = False


def candidate_regressors() -> dict[str, object]:
    """Unfitted regression algorithms compared for numeric-prediction tasks."""
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42),
        "SVR": SVR(kernel="rbf", C=10.0),
    }
    if _XGB:
        models["XGBoost"] = XGBRegressor(n_estimators=200, learning_rate=0.05, random_state=42, n_jobs=-1)
    return models


def candidate_classifiers() -> dict[str, object]:
    """Unfitted classification algorithms compared for label-prediction tasks."""
    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, random_state=42),
        "KNN": KNeighborsClassifier(n_neighbors=11),
        "Naive Bayes": GaussianNB(),
    }
    if _XGB:
        models["XGBoost"] = XGBClassifier(n_estimators=150, learning_rate=0.05, random_state=42, n_jobs=-1)
    return models
