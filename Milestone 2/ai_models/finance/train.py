"""
ai_models/finance/train.py
Training entry point for the finance domain (expense classifier).
"""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

from ai_models.common.training import train_and_persist
from ai_models.finance import model as fmodel
from ai_models.finance import preprocess as fprep
from ai_models.finance import synthetic as fsynth


def candidate_expense_classifiers() -> dict[str, object]:
    """Text-suitable classifiers (sparse TF-IDF friendly)."""
    return {
        "Naive Bayes": MultinomialNB(),
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "Linear SVM": LinearSVC(dual="auto", max_iter=5000),
        "Random Forest": RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42),
    }


def train_expense_classifier() -> dict:
    """Train and persist the best expense-category classifier."""
    data = fsynth.synthetic_expense_data()
    return train_and_persist(
        "finance", "expense_classifier", fmodel.EXPENSE_FEATURES, fmodel.EXPENSE_TARGET,
        data, fprep.build_expense_pipeline, candidate_expense_classifiers(),
        task="classification", display_name="Expense Classification",
    )


def train_all() -> dict:
    """Train every finance model and return a summary."""
    return {"expense_classifier": train_expense_classifier()}
