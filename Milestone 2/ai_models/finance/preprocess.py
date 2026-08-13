"""
ai_models/finance/preprocess.py
Text-classification pipeline for the finance domain (column selection +
TF-IDF + estimator).
"""

from __future__ import annotations

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


class _TextColumnSelector(BaseEstimator, TransformerMixin):
    """Extract a single text column from a dataframe as a 1-D string series."""

    def __init__(self, column: str):
        self.column = column

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.column].astype(str)


def build_expense_pipeline(algorithm: object) -> Pipeline:
    """Pipeline for classifying an expense description into a category."""
    return Pipeline(
        [
            ("text", _TextColumnSelector("description")),
            ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), max_features=5000)),
            ("model", algorithm),
        ]
    )
