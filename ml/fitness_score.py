"""
ml/fitness_score.py
--------------------
Computes a composite 0-100 "Fitness Score" from recent daily habits.
This is a transparent, weighted-rubric model (easy to explain to users
and to a project evaluator) rather than a black-box model, which is a
deliberate design choice for the "Habit & Lifestyle Analytics" module.

Weights:
    Steps           25%
    Sleep           20%
    Exercise        20%
    Hydration       15%
    Calorie balance 20%  (being close to TDEE, or a healthy deficit, scores well)
"""


def _score_steps(steps: float) -> float:
    return min(100, (steps / 10000) * 100)


def _score_sleep(hours: float) -> float:
    if hours <= 0:
        return 0
    ideal_low, ideal_high = 7, 9
    if ideal_low <= hours <= ideal_high:
        return 100
    diff = min(abs(hours - ideal_low), abs(hours - ideal_high))
    return max(0, 100 - diff * 20)


def _score_exercise(minutes: float) -> float:
    return min(100, (minutes / 45) * 100)


def _score_hydration(liters: float) -> float:
    return min(100, (liters / 2.5) * 100)


def _score_calorie_balance(consumed: float, tdee: float, goal: str) -> float:
    if tdee <= 0:
        return 50
    diff_pct = (consumed - tdee) / tdee * 100

    if goal == "weight_loss":
        # A 10-20% deficit is ideal; too aggressive or a surplus scores lower.
        if -20 <= diff_pct <= -10:
            return 100
        if -30 <= diff_pct < -20 or -10 < diff_pct <= 0:
            return 75
        return max(0, 75 - abs(diff_pct))
    elif goal == "muscle_gain":
        if 5 <= diff_pct <= 15:
            return 100
        return max(0, 100 - abs(diff_pct - 10) * 2)
    else:  # maintenance / endurance / general
        return max(0, 100 - abs(diff_pct) * 2)


def calculate_fitness_score(
    steps: float,
    sleep_hours: float,
    exercise_minutes: float,
    water_liters: float,
    calories_consumed: float,
    tdee: float,
    fitness_goal: str = "maintenance",
) -> float:
    steps_s = _score_steps(steps)
    sleep_s = _score_sleep(sleep_hours)
    exercise_s = _score_exercise(exercise_minutes)
    hydration_s = _score_hydration(water_liters)
    calorie_s = _score_calorie_balance(calories_consumed, tdee, fitness_goal)

    total = (
        steps_s * 0.25
        + sleep_s * 0.20
        + exercise_s * 0.20
        + hydration_s * 0.15
        + calorie_s * 0.20
    )
    return round(total, 1)
