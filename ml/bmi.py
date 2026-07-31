"""
ml/bmi.py
---------
Simple, well-established formulas used across the app:
  - BMI (Body Mass Index)
  - BMR (Basal Metabolic Rate) via the Mifflin-St Jeor equation
  - TDEE (Total Daily Energy Expenditure)
These are not "trained" models -- they are the deterministic building
blocks that feed the trained models (weight predictor, risk classifier).
"""


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    if not weight_kg or not height_cm:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def bmi_category(bmi: float) -> str:
    if bmi <= 0:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor Equation."""
    if gender and gender.lower().startswith("f"):
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,       # < 4000 steps/day
    "light": 1.375,         # 4000-7000 steps/day
    "moderate": 1.55,       # 7000-10000 steps/day
    "active": 1.725,        # 10000-14000 steps/day
    "very_active": 1.9,     # 14000+ steps/day
}


def activity_level_from_steps(steps: int) -> str:
    if steps < 4000:
        return "sedentary"
    if steps < 7000:
        return "light"
    if steps < 10000:
        return "moderate"
    if steps < 14000:
        return "active"
    return "very_active"


def calculate_tdee(bmr: float, steps: int) -> float:
    level = activity_level_from_steps(steps)
    return round(bmr * ACTIVITY_MULTIPLIERS[level], 1)
