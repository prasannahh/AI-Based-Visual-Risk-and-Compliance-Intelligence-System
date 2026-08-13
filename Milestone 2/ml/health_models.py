"""Transparent health calculations used by the application."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BMIResult:
    value: float
    category: str


@dataclass(frozen=True)
class CalorieResult:
    bmr_kcal: int
    maintenance_kcal: int
    target_kcal: int


def calculate_bmi(weight_kg: float, height_cm: float) -> BMIResult:
    """Calculate BMI and a standard adult BMI category."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive.")
    value = weight_kg / (height_cm / 100) ** 2
    category = "Underweight" if value < 18.5 else "Healthy range" if value < 25 else "Overweight" if value < 30 else "Obesity range"
    return BMIResult(round(value, 1), category)


def calorie_target(age: int, gender: str, weight_kg: float, height_cm: float, activity_level: str, goal: str) -> CalorieResult:
    """Estimate calories using Mifflin-St Jeor BMR and activity factors."""
    if age <= 0 or gender not in {"female", "male"}:
        raise ValueError("Use a positive age and gender of female or male.")
    sex_adjustment = 5 if gender == "male" else -161
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + sex_adjustment
    factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    if activity_level not in factors or goal not in {"maintain", "lose", "gain"}:
        raise ValueError("Invalid activity level or goal.")
    maintenance = bmr * factors[activity_level]
    adjustment = {"maintain": 0, "lose": -400, "gain": 300}[goal]
    return CalorieResult(round(bmr), round(maintenance), max(800, round(maintenance + adjustment)))


def fitness_score(steps: int, exercise_minutes: int, sleep_hours: float, water_litres: float) -> float:
    """Score daily behaviour from 0–100 with explainable weighted inputs."""
    values = (
        min(max(steps, 0) / 10000, 1) * 35,
        min(max(exercise_minutes, 0) / 45, 1) * 30,
        max(0, 1 - min(abs(sleep_hours - 8) / 4, 1)) * 25,
        min(max(water_litres, 0) / 2.5, 1) * 10,
    )
    return round(sum(values), 1)
