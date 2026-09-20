"""
ai_models/finance/model.py
Model registry for the finance domain.
"""

from __future__ import annotations

EXPENSE_CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Education", "Healthcare", "Savings", "Others"]

EXPENSE_FEATURES = ["description"]
EXPENSE_TARGET = "category"

BUDGET_SHARES = {"Food": 0.25, "Bills": 0.30, "Travel": 0.10, "Shopping": 0.10, "Healthcare": 0.10, "Education": 0.05, "Entertainment": 0.05, "Others": 0.05}
