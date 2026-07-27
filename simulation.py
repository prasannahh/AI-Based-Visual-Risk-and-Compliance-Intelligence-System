"""
simulation.py
--------------
The "Digital Twin Simulation Engine" (Module 4 / Milestone 3 in the plan).

Given a user's current profile and a hypothetical daily routine
(steps, sleep, calories consumed, exercise minutes), this simulates the
projected outcome after N days using the trained weight_predictor and the
deterministic fitness_score / risk_classifier logic -- exactly mirroring
how a real prediction is generated, just with hypothetical inputs instead
of logged history.
"""

from ml.bmi import calculate_bmi, calculate_bmr, calculate_tdee
from ml.weight_predictor import predict_weight_change
from ml.fitness_score import calculate_fitness_score
from ml.risk_classifier import predict_risks


def run_simulation(
    current_weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    fitness_goal: str,
    horizon_days: int,
    sim_steps: float,
    sim_sleep_hours: float,
    sim_calories_consumed: float,
    sim_exercise_minutes: float,
    sim_water_liters: float = 2.0,
) -> dict:
    """Run one what-if scenario and return the projected outcome."""

    bmr = calculate_bmr(current_weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, sim_steps)
    calorie_balance = sim_calories_consumed - tdee

    weight_change = predict_weight_change(
        current_weight_kg=current_weight_kg,
        height_cm=height_cm,
        age=age,
        gender=gender,
        avg_daily_calorie_balance=calorie_balance,
        avg_sleep_hours=sim_sleep_hours,
        avg_steps=sim_steps,
        horizon_days=horizon_days,
    )
    projected_weight = round(current_weight_kg + weight_change, 2)
    projected_bmi = calculate_bmi(projected_weight, height_cm)

    fitness_score = calculate_fitness_score(
        steps=sim_steps,
        sleep_hours=sim_sleep_hours,
        exercise_minutes=sim_exercise_minutes,
        water_liters=sim_water_liters,
        calories_consumed=sim_calories_consumed,
        tdee=tdee,
        fitness_goal=fitness_goal,
    )

    risks = predict_risks(
        bmi=projected_bmi,
        age=age,
        avg_steps=sim_steps,
        avg_sleep_hours=sim_sleep_hours,
    )

    return {
        "horizon_days": horizon_days,
        "tdee": round(tdee, 0),
        "daily_calorie_balance": round(calorie_balance, 0),
        "weight_change_kg": weight_change,
        "projected_weight_kg": projected_weight,
        "projected_bmi": projected_bmi,
        "fitness_score": fitness_score,
        "risks": risks,
    }


def compare_scenarios(base_scenario: dict, alt_scenario: dict) -> dict:
    """Compare a 'current path' scenario vs an 'improved lifestyle' scenario."""
    return {
        "weight_swing_kg": round(base_scenario["projected_weight_kg"] - alt_scenario["projected_weight_kg"], 2),
        "fitness_score_gain": round(alt_scenario["fitness_score"] - base_scenario["fitness_score"], 1),
        "bmi_change": round(base_scenario["projected_bmi"] - alt_scenario["projected_bmi"], 2),
    }
