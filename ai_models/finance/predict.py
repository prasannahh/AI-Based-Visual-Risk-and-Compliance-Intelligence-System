"""
ai_models/finance/predict.py
Prediction and recommendation APIs for the finance domain: expense
classification, spending analysis, savings prediction, budget recommendations
and future balance forecasting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai_models.common.utils import get_or_train
from ai_models.finance import model as fmodel
from ai_models.finance import train as ftrain


def _as_expense_frame(records_df: pd.DataFrame) -> pd.DataFrame:
    """Normalise financial records into a frame with date, category, amount
    and transaction_type (numeric amount, datetime date)."""
    if records_df is None or records_df.empty:
        return pd.DataFrame(columns=["date", "category", "amount", "transaction_type"])
    df = records_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    for col in ["category", "transaction_type"]:
        if col not in df.columns:
            df[col] = "Others"
    return df


def classify_expense(description: str) -> dict:
    """Classify a free-text expense description into a spending category.

    Returns:
        {'description', 'category', 'confidence'}.
    """
    model, _ = get_or_train("finance", "expense_classifier", ftrain.train_expense_classifier)
    frame = pd.DataFrame([[description]], columns=fmodel.EXPENSE_FEATURES)
    category = str(model.predict(frame)[0])
    proba = model.predict_proba(frame)[0] if hasattr(model, "predict_proba") else None
    confidence = float(proba.max()) if proba is not None else 0.0
    return {"description": description, "category": category, "confidence": round(confidence, 3)}


def spending_analysis(records_df: pd.DataFrame) -> dict:
    """Monthly, weekly and category-wise spending breakdown from financial
    records. Only rows with transaction_type == 'Expense' are counted.

    Returns:
        {'monthly': DataFrame, 'weekly': DataFrame,
         'category_wise': DataFrame, 'total_spent': float}.
    """
    df = _as_expense_frame(records_df)
    expenses = df[df["transaction_type"] == "Expense"] if not df.empty else df
    if expenses.empty:
        empty = pd.DataFrame()
        return {"monthly": empty, "weekly": empty, "category_wise": empty, "total_spent": 0.0}

    monthly = (
        expenses.groupby(expenses["date"].dt.to_period("M"))["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "month", "amount": "spent"})
    )
    weekly = (
        expenses.groupby(expenses["date"].dt.to_period("W"))["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "week", "amount": "spent"})
    )
    category_wise = (
        expenses.groupby("category")["amount"].sum().reset_index().rename(columns={"amount": "spent"})
        .sort_values("spent", ascending=False)
    )
    return {
        "monthly": monthly,
        "weekly": weekly,
        "category_wise": category_wise,
        "total_spent": round(float(expenses["amount"].sum()), 2),
    }


def predict_savings(records_df: pd.DataFrame, horizons: tuple[int, int, int, int] = (1, 3, 6, 12)) -> pd.DataFrame:
    """Forecast cumulative savings at fixed monthly horizons.

    Uses the linear trend of the user's historical monthly net change.

    Args:
        records_df: Financial records (date, amount, transaction_type...).
        horizons: Months ahead to forecast (default 1/3/6/12).

    Returns:
        DataFrame [months_ahead, predicted_savings].
    """
    df = _as_expense_frame(records_df)
    columns = ["months_ahead", "predicted_savings"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["net"] = df.apply(
        lambda r: r["amount"] if r["transaction_type"] in ("Income", "Savings") else -r["amount"],
        axis=1,
    )
    monthly = df.groupby(df["date"].dt.to_period("M"))["net"].sum().sort_index()
    current = float(df["net"].sum())
    if len(monthly) < 2:
        monthly_rate = float(monthly.iloc[0]) if not monthly.empty else 0.0
        rows = [{"months_ahead": h, "predicted_savings": round(current + monthly_rate * h, 2)} for h in horizons]
        return pd.DataFrame(rows, columns=columns)

    x = np.arange(len(monthly))
    slope, intercept = np.polyfit(x, monthly.to_numpy(dtype=float), 1)
    rows = []
    for h in horizons:
        future = current + sum(max(slope * (len(monthly) + i) + intercept, 0) for i in range(h))
        rows.append({"months_ahead": h, "predicted_savings": round(future, 2)})
    return pd.DataFrame(rows, columns=columns)


def recommend_budget(records_df: pd.DataFrame) -> dict:
    """Rule-based budget recommendation engine.

    Returns:
        {'monthly_budget', 'weekly_budget', 'emergency_fund', 'savings_goal',
         'category_limits': DataFrame, 'basis': str}.
    """
    df = _as_expense_frame(records_df)
    if df.empty:
        return {
            "monthly_budget": 0.0, "weekly_budget": 0.0, "emergency_fund": 0.0,
            "savings_goal": 0.0, "category_limits": pd.DataFrame(columns=["category", "limit"]),
            "basis": "Log income and expenses to unlock budget recommendations.",
        }

    months_active = max(df["date"].dt.to_period("M").nunique(), 1)
    monthly_income = float(df[df["transaction_type"] == "Income"]["amount"].sum()) / months_active
    monthly_expense = float(df[df["transaction_type"] == "Expense"]["amount"].sum()) / months_active

    if monthly_income > 0:
        monthly_budget = monthly_expense if monthly_expense > 0 else 0.6 * monthly_income
        emergency_fund = 6.0 * monthly_expense if monthly_expense > 0 else 3.0 * monthly_income
        savings_goal = 0.2 * monthly_income
        basis = "Estimated from your logged income and expenses."
    else:
        monthly_budget = monthly_expense
        emergency_fund = 6.0 * monthly_expense
        savings_goal = monthly_expense * 0.1
        basis = "Estimated from your logged expenses (no income logged yet)."

    limits = pd.DataFrame([{"category": c, "limit": round(monthly_budget * share, 2)} for c, share in fmodel.BUDGET_SHARES.items()])
    return {
        "monthly_budget": round(monthly_budget, 2),
        "weekly_budget": round(monthly_budget / 4.3, 2),
        "emergency_fund": round(emergency_fund, 2),
        "savings_goal": round(savings_goal, 2),
        "category_limits": limits,
        "basis": basis,
    }


def predict_future_balance(
    records_df: pd.DataFrame,
    days: int = 365,
    predicted_monthly_savings: float | None = None,
) -> pd.DataFrame:
    """Forecast account balance derived from the Savings Prediction model output.

    Formula:
        projected_balance(d) = current_balance + (predicted_monthly_savings * d / 30.0)

    Args:
        records_df: Financial records (date, amount, transaction_type...).
        days: Forecast horizon in days.
        predicted_monthly_savings: Optional explicit monthly savings prediction.
            If None, derived from predict_savings(records_df).

    Returns:
        DataFrame [date, predicted_balance]. Empty if records_df is empty or
        savings prediction is unavailable.
    """
    df = _as_expense_frame(records_df)
    columns = ["date", "predicted_balance"]
    if df.empty:
        return pd.DataFrame(columns=columns)

    df["net"] = df.apply(
        lambda r: r["amount"] if r["transaction_type"] in ("Income", "Savings") else -r["amount"],
        axis=1,
    )
    current_balance = float(df["net"].sum())

    if predicted_monthly_savings is None:
        savings_df = predict_savings(records_df, horizons=(1,))
        if savings_df.empty or "predicted_savings" not in savings_df.columns or len(savings_df) == 0:
            return pd.DataFrame(columns=columns)
        predicted_monthly_savings = float(savings_df["predicted_savings"].iloc[0]) - current_balance

    start = df["date"].max() if pd.notna(df["date"].max()) else pd.Timestamp.now()
    future_dates = pd.date_range(start=start + pd.Timedelta(days=1), periods=days, freq="D")

    day_indices = np.arange(1, days + 1)
    projected_balances = current_balance + (predicted_monthly_savings * day_indices / 30.0)

    return pd.DataFrame(
        {
            "date": future_dates,
            "predicted_balance": projected_balances.round(2),
        }
    )

