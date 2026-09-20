"""
simulation/scenarios.py
Scenario generation for "what-if" decision simulation.

For each domain, generates a baseline scenario (current plan) plus
multiple alternative scenarios with different decision parameters.
Supports both automatic generation and user-defined custom scenarios.
"""

from __future__ import annotations


def generate_financial_scenarios(
    monthly_income: float,
    monthly_expenses: float,
    monthly_saving: float,
    current_savings: float,
    custom_scenarios: list[dict] | None = None,
) -> list[dict]:
    """Generate financial decision scenarios.

    Creates a baseline (current plan) plus alternatives:
    - Increase savings by 25%
    - Increase savings by 50%
    - Reduce expenses by 15%

    Custom scenarios override auto-generated alternatives.

    Returns:
        List of dicts with keys: name, description, monthly_expenses,
        monthly_saving, is_baseline.
    """
    scenarios = []

    scenarios.append({
        "name": "Current Plan",
        "description": f"Continue saving \u20b9{monthly_saving:,.0f}/month",
        "monthly_expenses": monthly_expenses,
        "monthly_saving": monthly_saving,
        "is_baseline": True,
    })

    if custom_scenarios:
        for cs in custom_scenarios:
            scenarios.append({
                "name": cs.get("name", "Custom Scenario"),
                "description": cs.get("description", ""),
                "monthly_expenses": cs.get("monthly_expenses", monthly_expenses),
                "monthly_saving": cs.get("monthly_saving", monthly_saving),
                "is_baseline": False,
            })
    else:
        increase_25 = round(monthly_saving * 1.25, 2)
        increase_50 = round(monthly_saving * 1.50, 2)
        reduce_expenses = round(monthly_expenses * 0.85, 2)
        expense_reduction_savings = round(monthly_saving + (monthly_expenses - reduce_expenses), 2)

        scenarios.append({
            "name": "Save +25%",
            "description": f"Increase savings to \u20b9{increase_25:,.0f}/month (+25%)",
            "monthly_expenses": monthly_expenses,
            "monthly_saving": increase_25,
            "is_baseline": False,
        })

        scenarios.append({
            "name": "Save +50%",
            "description": f"Increase savings to \u20b9{increase_50:,.0f}/month (+50%)",
            "monthly_expenses": monthly_expenses,
            "monthly_saving": increase_50,
            "is_baseline": False,
        })

        scenarios.append({
            "name": "Cut Expenses 15%",
            "description": f"Reduce expenses to \u20b9{reduce_expenses:,.0f}/month, save \u20b9{expense_reduction_savings:,.0f}/month",
            "monthly_expenses": reduce_expenses,
            "monthly_saving": expense_reduction_savings,
            "is_baseline": False,
        })

    return scenarios


def generate_study_scenarios(
    current_hours: float,
    custom_scenarios: list[dict] | None = None,
) -> list[dict]:
    """Generate study decision scenarios.

    Creates a baseline (current study hours) plus alternatives.

    Returns:
        List of dicts with keys: name, description, hours_per_day, is_baseline.
    """
    scenarios = []

    scenarios.append({
        "name": f"Current ({current_hours:.1f}h/day)",
        "description": f"Continue studying {current_hours:.1f} hours per day",
        "hours_per_day": current_hours,
        "is_baseline": True,
    })

    if custom_scenarios:
        for cs in custom_scenarios:
            scenarios.append({
                "name": cs.get("name", "Custom Study Scenario"),
                "description": cs.get("description", ""),
                "hours_per_day": cs.get("hours_per_day", current_hours),
                "is_baseline": False,
            })
    else:
        alternatives = []
        if current_hours < 4:
            alternatives.append(current_hours + 1)
        alternatives.append(max(current_hours + 1, 4.0))
        alternatives.append(max(current_hours + 2, 5.0))
        alternatives.append(max(current_hours + 3, 6.0))

        seen = set()
        for h in alternatives:
            h = round(h, 1)
            if h not in seen and h != current_hours:
                seen.add(h)
                diff = h - current_hours
                scenarios.append({
                    "name": f"Study {h:.1f}h/day (+{diff:.1f}h)",
                    "description": f"Increase to {h:.1f} hours per day",
                    "hours_per_day": h,
                    "is_baseline": False,
                })

    return scenarios


def generate_habit_scenarios(
    current_completion_rate: float,
    exercise_frequency: int,
    custom_scenarios: list[dict] | None = None,
) -> list[dict]:
    """Generate habit/fitness decision scenarios.

    Creates a baseline (current habits) plus alternatives with
    increased exercise frequency and completion rates.

    Returns:
        List of dicts with keys: name, description, completion_rate,
        exercise_frequency, is_baseline.
    """
    scenarios = []

    scenarios.append({
        "name": "Current Habits",
        "description": f"Current completion: {current_completion_rate:.0f}%, exercise: {exercise_frequency} days/week",
        "completion_rate": current_completion_rate,
        "exercise_frequency": exercise_frequency,
        "is_baseline": True,
    })

    if custom_scenarios:
        for cs in custom_scenarios:
            scenarios.append({
                "name": cs.get("name", "Custom Habit Scenario"),
                "description": cs.get("description", ""),
                "completion_rate": cs.get("completion_rate", current_completion_rate),
                "exercise_frequency": cs.get("exercise_frequency", exercise_frequency),
                "is_baseline": False,
            })
    else:
        new_freq_1 = min(exercise_frequency + 1, 7)
        new_freq_2 = min(exercise_frequency + 2, 7)
        improved_rate = min(current_completion_rate + 15, 100)

        scenarios.append({
            "name": f"+1 Exercise Day ({new_freq_1}/week)",
            "description": f"Increase exercise to {new_freq_1} days/week",
            "completion_rate": current_completion_rate,
            "exercise_frequency": new_freq_1,
            "is_baseline": False,
        })

        scenarios.append({
            "name": f"+2 Exercise Days ({new_freq_2}/week)",
            "description": f"Increase exercise to {new_freq_2} days/week",
            "completion_rate": current_completion_rate,
            "exercise_frequency": new_freq_2,
            "is_baseline": False,
        })

        scenarios.append({
            "name": f"Improve Consistency ({improved_rate:.0f}%)",
            "description": f"Increase habit completion to {improved_rate:.0f}%",
            "completion_rate": improved_rate,
            "exercise_frequency": exercise_frequency,
            "is_baseline": False,
        })

    return scenarios
