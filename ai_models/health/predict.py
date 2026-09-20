"""
ai_models/health/predict.py
Prediction and recommendation APIs for the health domain.

All functions load the persisted model automatically (training it on demand
the first time) and return plain dicts / dataframes, so the Streamlit layer
can log each prediction back to PostgreSQL.
"""

from __future__ import annotations

import pandas as pd

from ai_models.common.utils import get_or_train
from ai_models.health import model as hmodel
from ai_models.health import train as htrain

BMI_SUGGESTIONS = {
    "Underweight": [
        "Increase daily calorie intake with nutrient-dense foods.",
        "Add strength training to build lean muscle mass.",
        "Consider a clinician review to rule out underlying causes.",
    ],
    "Healthy range": [
        "Keep a balanced diet with adequate protein and fibre.",
        "Maintain a steady sleep routine of 7-9 hours.",
        "Continue regular aerobic + resistance exercise.",
    ],
    "Overweight": [
        "Aim for a modest calorie deficit of 300-500 kcal/day.",
        "Add 30-60 minutes of moderate exercise most days.",
        "Track weight weekly and review progress monthly.",
    ],
    "Obesity range": [
        "Consult a qualified clinician before starting any plan.",
        "Focus on gradual, sustainable lifestyle changes first.",
        "Pair nutrition guidance with supervised physical activity.",
    ],
}

RISK_RECOMMENDATIONS = {
    "Obesity": [
        "Reduce portion sizes and ultra-processed foods.",
        "Target a modest weekly weight-loss rate of 0.5-1 kg.",
        "Combine aerobic exercise with strength training 3-5x/week.",
    ],
    "Diabetes": [
        "Prioritise low-glycaemic foods and fibre.",
        "Get at least 30 minutes of moderate activity daily.",
        "Monitor fasting glucose annually if in a high-risk range.",
    ],
    "Hypertension": [
        "Reduce sodium intake and increase potassium-rich foods.",
        "Aim for 150 minutes/week of moderate exercise.",
        "Manage stress and keep alcohol consumption low.",
    ],
}


def assess_bmi(age: int, gender: str, height_cm: float, weight_kg: float) -> dict:
    """Rule-based BMI assessment with category and lifestyle suggestions.

    Args:
        age: User age (years).
        gender: 'male' or 'female'.
        height_cm: Height in cm.
        weight_kg: Weight in kg.

    Returns:
        {'age', 'gender', 'bmi', 'category', 'suggestions'}.
    """
    from ai_models.common.feature_engineering import bmi as bmi_value
    from ai_models.common.feature_engineering import bmi_category

    value = round(bmi_value(weight_kg, height_cm), 1)
    category = bmi_category(value)
    return {
        "age": int(age),
        "gender": gender,
        "bmi": value,
        "category": category,
        "suggestions": BMI_SUGGESTIONS[category],
    }


def predict_calorie_requirement(age: int, gender: str, height_cm: float, weight_kg: float, activity_level: str) -> dict:
    """Predict the daily calorie requirement (ML estimate + Mifflin-St Jeor).

    Args:
        age: User age (years).
        gender: 'male' or 'female'.
        height_cm: Height in cm.
        weight_kg: Weight in kg.
        activity_level: one of sedentary/light/moderate/active/very_active.

    Returns:
        {'ml_kcal', 'mifflin_bmr_kcal', 'maintenance_kcal'}.
    """
    from ai_models.common.feature_engineering import activity_multiplier, mifflin_st_jeor

    model, _ = get_or_train("health", "calorie_predictor", htrain.train_calorie_model)
    frame = pd.DataFrame(
        [{"age": age, "gender": gender, "height_cm": height_cm, "weight_kg": weight_kg, "activity_level": activity_level}],
        columns=hmodel.CALORIE_FEATURES,
    )
    ml_kcal = max(1200.0, float(model.predict(frame)[0]))
    bmr = mifflin_st_jeor(age, gender, weight_kg, height_cm)
    return {
        "ml_kcal": round(ml_kcal),
        "mifflin_bmr_kcal": round(bmr),
        "maintenance_kcal": round(bmr * activity_multiplier(activity_level)),
    }


def predict_weight_forecast(age: int, gender: str, height_cm: float, current_weight_kg: float, activity_level: str, daily_calories: int, days: int = 30) -> pd.DataFrame:
    """Iteratively forecast weight over the next `days` days.

    Each day's predicted weight becomes the input to the next prediction,
    simulating the compounding effect of a calorie balance.

    Args:
        age/gender/height_cm/current_weight_kg/activity_level/daily_calories:
            User profile inputs.
        days: Forecast horizon (days).

    Returns:
        DataFrame [day, predicted_weight_kg].
    """
    model, _ = get_or_train("health", "weight_predictor", htrain.train_weight_model)
    rows, weight = [], float(current_weight_kg)
    for day in range(1, days + 1):
        frame = pd.DataFrame(
            [
                {
                    "age": age,
                    "gender": gender,
                    "height_cm": height_cm,
                    "current_weight_kg": weight,
                    "activity_level": activity_level,
                    "daily_calories": daily_calories,
                }
            ],
            columns=hmodel.WEIGHT_FEATURES,
        )
        weight = max(25.0, float(model.predict(frame)[0]))
        rows.append({"day": day, "predicted_weight_kg": round(weight, 2)})
    return pd.DataFrame(rows)


def predict_health_risks(age: int, gender: str, height_cm: float, weight_kg: float, activity_level: str, daily_calories: int, exercise_frequency: int = 3) -> list[dict]:
    """Predict probabilities for obesity, diabetes and hypertension.

    Args:
        age: User age (years).
        gender: 'male' or 'female'.
        height_cm: Height in cm.
        weight_kg: Weight in kg.
        activity_level: Activity level string.
        daily_calories: Average daily calorie intake.
        exercise_frequency: Exercise days per week.

    Returns:
        List of {'disease', 'probability_pct', 'risk_level', 'recommendations'}.
    """
    from ai_models.common.feature_engineering import bmi as bmi_value

    risk_bmi = round(bmi_value(weight_kg, height_cm), 1)
    outcomes = []
    for label, display in hmodel.RISK_LABELS.items():
        model, _ = get_or_train("health", label, lambda: htrain.train_risk_models()[label])
        frame = pd.DataFrame(
            [
                {
                    "age": age,
                    "gender": gender,
                    "height_cm": height_cm,
                    "weight_kg": weight_kg,
                    "activity_level": activity_level,
                    "daily_calories": daily_calories,
                    "exercise_frequency": exercise_frequency,
                }
            ],
            columns=hmodel.RISK_FEATURES,
        )
        probability = float(model.predict_proba(frame)[0][1]) * 100
        risk_level = "Low" if probability < 30 else "Moderate" if probability < 60 else "High"
        outcomes.append(
            {
                "disease": display,
                "probability_pct": round(probability, 1),
                "risk_level": risk_level,
                "bmi": risk_bmi,
                "recommendations": RISK_RECOMMENDATIONS[display],
            }
        )
    return outcomes
