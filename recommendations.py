"""
recommendations.py
-------------------
Module 5: Recommendation System.
Generates personalized, actionable recommendations from a user's recent
averages, fitness goal, and computed risk levels. Each recommendation is
tagged with a category and priority so the dashboard can sort/filter them.
"""


def generate_recommendations(
    avg_steps: float,
    avg_sleep_hours: float,
    avg_water_liters: float,
    avg_exercise_minutes: float,
    calorie_balance: float,
    fitness_goal: str,
    risks: dict,
) -> list:
    recs = []

    # --- Activity ---
    if avg_steps < 7000:
        recs.append({
            "category": "exercise",
            "priority": "high" if avg_steps < 4000 else "medium",
            "text": f"You're averaging {int(avg_steps)} steps/day. Aim to add "
                    f"{max(1000, 8000 - int(avg_steps))} more steps daily "
                    f"(a 15-20 min walk) to reach a healthier activity zone."
        })
    else:
        recs.append({
            "category": "exercise",
            "priority": "low",
            "text": "Great job staying active! Maintain your current step count "
                    "and consider adding 1-2 strength training sessions per week."
        })

    if avg_exercise_minutes < 30:
        recs.append({
            "category": "exercise",
            "priority": "medium",
            "text": "Try to reach at least 30 minutes of structured exercise "
                    "most days (brisk walking, cycling, or a home workout)."
        })

    # --- Sleep ---
    if avg_sleep_hours < 7:
        recs.append({
            "category": "sleep",
            "priority": "high" if avg_sleep_hours < 6 else "medium",
            "text": f"You're averaging {avg_sleep_hours:.1f} hrs of sleep. "
                    "Poor sleep slows recovery and can increase appetite/weight "
                    "gain risk. Try shifting your bedtime 30 minutes earlier."
        })
    elif avg_sleep_hours > 9.5:
        recs.append({
            "category": "sleep",
            "priority": "low",
            "text": "You're sleeping more than typical recommendations (7-9 hrs). "
                    "If you still feel tired, it may be worth discussing with a doctor."
        })

    # --- Hydration ---
    if avg_water_liters < 2.0:
        recs.append({
            "category": "hydration",
            "priority": "medium",
            "text": f"You're drinking about {avg_water_liters:.1f}L/day. "
                    "Aim for at least 2-2.5L to support metabolism and energy levels."
        })

    # --- Nutrition / calorie balance vs goal ---
    if fitness_goal == "weight_loss":
        if calorie_balance > -300:
            recs.append({
                "category": "nutrition",
                "priority": "high",
                "text": "Your calorie intake is close to (or above) your maintenance "
                        "level. For steady weight loss, target roughly a 300-500 "
                        "kcal/day deficit."
            })
        elif calorie_balance < -800:
            recs.append({
                "category": "nutrition",
                "priority": "medium",
                "text": "Your calorie deficit looks quite aggressive. Very large "
                        "deficits are hard to sustain and can affect energy levels — "
                        "consider moderating it to 300-500 kcal/day below maintenance."
            })
        else:
            recs.append({
                "category": "nutrition",
                "priority": "low",
                "text": "Your calorie deficit is in a healthy, sustainable range "
                        "for gradual weight loss. Keep it up!"
            })
    elif fitness_goal == "muscle_gain":
        if calorie_balance < 0:
            recs.append({
                "category": "nutrition",
                "priority": "medium",
                "text": "You're in a calorie deficit, which makes it harder to "
                        "build muscle. Consider a small surplus (~200-300 kcal/day) "
                        "paired with resistance training and adequate protein."
            })

    # --- Risk alerts ---
    for risk_name, info in risks.items():
        if info["level"] in ("Medium", "High"):
            recs.append({
                "category": "risk_alert",
                "priority": "high" if info["level"] == "High" else "medium",
                "text": f"Your predicted {risk_name} risk is currently "
                        f"{info['level']} ({int(info['probability']*100)}% model "
                        "confidence). This is an educational estimate, not a "
                        "diagnosis — consider discussing your habits with a "
                        "healthcare professional."
            })

    return recs
