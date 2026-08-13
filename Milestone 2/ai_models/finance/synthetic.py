"""
ai_models/finance/synthetic.py
Synthetic expense-description generator used to train and validate the
expense classifier. Replace with real, anonymised transaction descriptions
before production use.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ai_models.finance import model as fmodel

_TEMPLATES = {
    "Food": [
        "grocery store shopping",
        "restaurant dinner with friends",
        "morning coffee at the cafe",
        "swiggy food delivery",
        "pizza night takeaway",
        "lunch at office canteen",
        "supermarket weekly run",
        "bakery bread and snacks",
    ],
    "Travel": [
        "uber ride to the station",
        "flight ticket to the city",
        "metro card recharge",
        "monthly train pass",
        "petrol fill at fuel station",
        "taxi fare home",
        "bus ticket journey",
        "parking fee downtown",
    ],
    "Shopping": [
        "amazon order delivery",
        "flipkart electronics purchase",
        "clothing store new jacket",
        "new phone installment",
        "running shoes at the outlet",
        "mall shopping spree",
        "home decor purchase",
        "gadget accessories buy",
    ],
    "Bills": [
        "electricity bill payment",
        "internet bill recharge",
        "water bill monthly",
        "apartment rent transfer",
        "mobile recharge plan",
        "gas cylinder booking",
        "wifi broadband bill",
        "property maintenance fee",
    ],
    "Entertainment": [
        "movie tickets weekend",
        "netflix subscription",
        "spotify premium",
        "concert tickets booking",
        "video game purchase",
        "theatre play evening",
        "amusement park entry",
        "streaming platform plan",
    ],
    "Education": [
        "tuition fee payment",
        "online course enrollment",
        "reference books purchase",
        "certification exam fee",
        "college semester fee",
        "stationery and notebooks",
        "workshop registration",
        "language class fee",
    ],
    "Healthcare": [
        "pharmacy medicines",
        "doctor consultation fee",
        "hospital bill settlement",
        "vitamins and supplements",
        "health insurance premium",
        "dental checkup",
        "physiotherapy session",
        "blood test lab charges",
    ],
    "Savings": [
        "monthly savings transfer",
        "mutual fund sip investment",
        "fixed deposit opening",
        "emergency fund top up",
        "recurring deposit contribution",
        "stock purchase allocation",
    ],
}


def synthetic_expense_data(rows: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Generate description -> category pairs for classifier training."""
    rng = np.random.default_rng(seed)
    categories = list(_TEMPLATES.keys())
    descriptions, labels = [], []
    for _ in range(rows):
        category = rng.choice(categories)
        base = rng.choice(_TEMPLATES[category])
        description = f"{base} {rng.choice(['paid via card', 'cash payment', 'upi transfer', 'online', '', '', ''])}".strip()
        descriptions.append(description)
        labels.append(category)
    return pd.DataFrame({"description": descriptions, "category": labels})
