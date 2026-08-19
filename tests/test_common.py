"""Tests for the shared AI utilities (metrics, cleaning, feature engineering)."""

import numpy as np
import pandas as pd

from ai_models.common import data_cleaning as dc
from ai_models.common import feature_engineering as fe
from ai_models.common import metrics as m


def test_fill_missing_mean():
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [10, 20, 30]})
    out = dc.fill_missing(df, columns=["a"], strategy="mean")
    assert out["a"].iloc[1] == 2.0
    assert len(out) == len(df)


def test_fill_missing_constant():
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0]})
    out = dc.fill_missing(df, columns=["a"], strategy="constant", constant=7.0)
    assert out["a"].iloc[1] == 7.0


def test_remove_outliers_iqr():
    df = pd.DataFrame({"x": list(range(1, 11)) + [1000]})
    out = dc.remove_outliers(df, columns=["x"], method="iqr")
    assert 1000 not in out["x"].values


def test_standardize():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    out, scaler = dc.standardize(df, columns=["x"])
    assert abs(out["x"].mean()) < 1e-9
    assert abs(out["x"].std(ddof=0) - 1.0) < 1e-9


def test_normalize():
    df = pd.DataFrame({"x": [10.0, 20.0, 30.0]})
    out, scaler = dc.normalize(df, columns=["x"])
    assert out["x"].min() == 0.0 and out["x"].max() == 1.0


def test_regression_metrics():
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.0, 3.0, 3.9])
    metrics = m.regression_metrics(y_true, y_pred)
    assert set(["mae", "mse", "rmse", "r2"]) <= set(metrics)
    assert metrics["mae"] >= 0


def test_classification_metrics_binary():
    y_true = np.array([0, 1, 1, 1, 0])
    y_pred = np.array([0, 1, 0, 1, 0])
    proba = np.array([[0.8, 0.2], [0.2, 0.8], [0.6, 0.4], [0.3, 0.7], [0.9, 0.1]])
    metrics = m.classification_metrics(y_true, y_pred, proba)
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["roc_auc"] <= 1


def test_classification_metrics_multiclass():
    y_true = np.array(["a", "b", "c", "a", "b"])
    y_pred = np.array(["a", "b", "c", "a", "b"])
    proba = np.eye(5)[[0, 1, 2, 0, 1]]
    metrics = m.classification_metrics(y_true, y_pred, proba)
    assert metrics["accuracy"] == 1.0
    assert metrics["f1"] == 1.0


def test_compare_regressors_returns_ranked_table():
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression

    x = np.random.default_rng(0).normal(size=(200, 3))
    y = x[:, 0] * 2 - x[:, 1] + 1
    results = m.compare_regressors(
        {"LR": LinearRegression(), "RF": RandomForestRegressor(n_estimators=20, random_state=42)},
        x[:150], y[:150], x[150:], y[150:], cv=2,
    )
    assert "model" in results.columns and "best" in results.columns
    assert results["best"].sum() == 1


def test_compare_classifiers_returns_ranked_table():
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB

    rng = np.random.default_rng(0)
    x = rng.normal(size=(300, 2))
    y = (x[:, 0] + x[:, 1] > 0).astype(int)
    results = m.compare_classifiers(
        {"NB": GaussianNB(), "LR": LogisticRegression(max_iter=1000)},
        x[:200], y[:200], x[200:], y[200:], cv=2,
    )
    assert "model" in results.columns and "best" in results.columns


def test_mifflin_st_jeor_male_vs_female():
    male = fe.mifflin_st_jeor(30, "male", 70, 175)
    female = fe.mifflin_st_jeor(30, "female", 70, 175)
    assert male > female


def test_bmi_category():
    assert fe.bmi_category(17.0) == "Underweight"
    assert fe.bmi_category(22.0) == "Healthy range"
    assert fe.bmi_category(27.0) == "Overweight"
    assert fe.bmi_category(33.0) == "Obesity range"


def test_performance_to_gpa():
    assert fe.performance_to_gpa(95) == 4.0
    assert fe.performance_to_gpa(35) == 0.0


def test_add_date_features():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=5)})
    out = fe.add_date_features(df)
    assert "weekday" in out.columns and "month" in out.columns
