"""Tests for the finance AI module."""

import pandas as pd

from ai_models.finance import evaluate as feval
from ai_models.finance import predict as fpredict


def _records():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05"]
            ),
            "amount": [250.0, 45.0, 1200.0, 90.0, 500.0],
            "transaction_type": ["Expense", "Expense", "Income", "Expense", "Expense"],
            "category": ["Food", "Transport", "Salary", "Entertainment", "Utilities"],
            "description": ["lunch", "cab ride", "salary credit", "movie", "electricity bill"],
        }
    )


def test_classify_expense():
    result = fpredict.classify_expense("Electricity bill for June")
    assert result["description"] == "Electricity bill for June"
    assert isinstance(result["category"], str) and result["category"]
    assert 0 <= result["confidence"] <= 1


def test_spending_analysis_structure():
    analysis = fpredict.spending_analysis(_records())
    assert analysis["total_spent"] == 885.0
    assert not analysis["monthly"].empty
    assert not analysis["weekly"].empty
    assert not analysis["category_wise"].empty
    assert list(analysis["category_wise"].columns) == ["category", "spent"]


def test_predict_savings():
    forecast = fpredict.predict_savings(_records())
    assert list(forecast.columns) == ["months_ahead", "predicted_savings"]
    assert len(forecast) == 4


def test_recommend_budget():
    budget = fpredict.recommend_budget(_records())
    assert budget["monthly_budget"] > 0
    assert budget["savings_goal"] > 0
    assert budget["basis"]
    assert not budget["category_limits"].empty


def test_predict_future_balance():
    balance = fpredict.predict_future_balance(_records(), days=30)
    assert list(balance.columns) == ["date", "predicted_balance"]
    assert len(balance) == 30

    # Test formula matching: current_balance + (predicted_monthly_savings * days / 30)
    records = _records()
    records["net"] = records.apply(
        lambda r: r["amount"] if r["transaction_type"] in ("Income", "Savings") else -r["amount"],
        axis=1,
    )
    current_balance = float(records["net"].sum())
    monthly_savings = 5000.0
    balance_custom = fpredict.predict_future_balance(records, days=90, predicted_monthly_savings=monthly_savings)
    expected_last_point = round(current_balance + (monthly_savings * 90 / 30.0), 2)
    assert balance_custom["predicted_balance"].iloc[-1] == expected_last_point

    # Test empty dataframe handling
    empty_balance = fpredict.predict_future_balance(pd.DataFrame(), days=30)
    assert empty_balance.empty


def test_saved_metrics_after_train():
    metrics = feval.saved_model_metrics()
    assert "expense_classifier" in metrics

