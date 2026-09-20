"""
ai_models/common/feature_engineering.py
Shared feature-building helpers: activity factors, BMR/BMI formulas,
date-based features, rolling/lag features and score-to-GPA conversions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

ACTIVITY_BURN = {"sedentary": 0, "light": 150, "moderate": 300, "active": 500, "very_active": 700}


def activity_multiplier(level: str) -> float:
    """Total daily energy expenditure multiplier for a given activity level."""
    return ACTIVITY_FACTORS.get(level, 1.2)


def activity_burn(level: str) -> float:
    """Approximate extra kcal burned per day for a given activity level."""
    return ACTIVITY_BURN.get(level, 0)


def mifflin_st_jeor(age, gender, weight_kg, height_cm):
    """Basal metabolic rate (kcal/day) using the Mifflin-St Jeor equation.

    Vectorised: accepts scalars or numpy/pandas arrays for `gender`.
    """
    sex_adjustment = np.where(np.asarray(gender) == "male", 5, -161)
    return 10 * np.asarray(weight_kg) + 6.25 * np.asarray(height_cm) - 5 * np.asarray(age) + sex_adjustment


def bmi(weight_kg: float, height_cm: float) -> float:
    """Body Mass Index from weight (kg) and height (cm)."""
    return weight_kg / (height_cm / 100) ** 2


def bmi_category(value: float) -> str:
    """Standard adult BMI category for a computed BMI value."""
    if value < 18.5:
        return "Underweight"
    if value < 25:
        return "Healthy range"
    if value < 30:
        return "Overweight"
    return "Obesity range"


def add_date_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Append calendar features (weekday, month, day-of-year) for a date column."""
    out = df.copy()
    dates = pd.to_datetime(out[date_col])
    out["weekday"] = dates.dt.weekday
    out["month"] = dates.dt.month
    out["day_of_year"] = dates.dt.dayofyear
    return out


def add_rolling(df: pd.DataFrame, value_col: str, window: int = 7) -> pd.DataFrame:
    """Append rolling-mean features for a value column (requires a date column)."""
    out = df.copy()
    dates = pd.to_datetime(out["date"])
    out = out.sort_values("date").reset_index(drop=True)
    out[f"{value_col}_roll{window}"] = out[value_col].rolling(window, min_periods=1).mean()
    out["date"] = dates
    return out


def performance_to_gpa(score: float) -> float:
    """Convert a 0-100 percentage score into a standard 4.0 GPA."""
    if score >= 90:
        return 4.0
    if score >= 80:
        return 3.7
    if score >= 70:
        return 3.0
    if score >= 60:
        return 2.3
    if score >= 50:
        return 1.7
    if score >= 40:
        return 1.0
    return 0.0
