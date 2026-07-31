"""
chatbot.py
----------
Module 6 (part 2): Conversational AI assistant.

If an OPENAI_API_KEY is set in .env, questions are answered by GPT with the
user's live digital-twin context injected into the prompt (grounded,
personalized answers). Otherwise, a built-in rule-based responder handles
common questions using the same data -- so the app works fully offline
with zero API keys, which matters since PostgreSQL + local setup is
already required.
"""

import os
import re


def _build_context_string(context: dict) -> str:
    return (
        f"User profile: age={context.get('age')}, gender={context.get('gender')}, "
        f"height={context.get('height_cm')}cm, weight={context.get('weight_kg')}kg, "
        f"goal={context.get('fitness_goal')}.\n"
        f"Latest prediction: BMI={context.get('bmi')}, "
        f"fitness_score={context.get('fitness_score')}, "
        f"predicted weight in 30 days={context.get('predicted_weight_30d')}kg, "
        f"risks={context.get('risks')}."
    )


def _rule_based_answer(question: str, context: dict) -> str:
    q = question.lower()

    if re.search(r"\bbmi\b", q):
        return (f"Your current BMI is {context.get('bmi', 'N/A')}. "
                f"A BMI between 18.5 and 25 is generally considered the normal range.")

    if "fitness score" in q or "score" in q:
        return (f"Your current fitness score is {context.get('fitness_score', 'N/A')}/100, "
                "based on your steps, sleep, exercise, hydration, and calorie balance.")

    if "goal" in q or ("weight" in q and ("reach" in q or "will i" in q or "achieve" in q)):
        predicted = context.get("predicted_weight_30d")
        goal = context.get("fitness_goal", "your goal")
        if predicted:
            return (f"Based on your current habits, your Digital Twin projects a weight "
                    f"of about {predicted}kg. Head to the **Digital Twin Simulation** tab "
                    f"to test specific changes (steps, sleep, calories) and see exactly "
                    f"how close they'd get you to your {goal.replace('_', ' ')} goal.")
        return ("I don't have a recent prediction yet -- log a few days of data, then "
                "check the **AI Predictions** or **Digital Twin Simulation** tabs to see "
                "a personalized projection toward your goal.")

    if "weight" in q and ("lose" in q or "loss" in q):
        return ("To lose weight sustainably, aim for a 300-500 kcal/day deficit, "
                "7-9 hours of sleep, and at least 8,000-10,000 steps per day. "
                "Try the Simulation tab to see a personalized 'what-if' projection!")

    if "weight" in q and ("gain" in q or "muscle" in q):
        return ("To gain weight/muscle, aim for a modest 200-300 kcal/day surplus "
                "combined with resistance training 3-4x/week and enough protein "
                "(roughly 1.6-2.2g per kg of body weight).")

    if "sleep" in q:
        return ("Most adults need 7-9 hours of sleep. Poor sleep is linked to "
                "higher appetite, slower recovery, and increased weight-gain risk "
                "in your digital twin's predictions.")

    if "risk" in q or "diabetes" in q or "hypertension" in q or "obesity" in q:
        risks = context.get("risks", {})
        if risks:
            lines = [f"- {name}: {info['level']} risk" for name, info in risks.items()]
            return "Your latest predicted risk levels are:\n" + "\n".join(lines) + \
                   "\n\n(This is an educational estimate, not a medical diagnosis.)"
        return "Log some daily health data first so I can estimate your risk levels."

    if "steps" in q:
        return ("10,000 steps/day is a commonly used activity target. Even "
                "increasing from a sedentary baseline to 7,000-8,000 steps/day "
                "produces meaningful health benefits.")

    if "water" in q or "hydration" in q:
        return "Aim for roughly 2-2.5 liters of water per day, more if you exercise heavily or it's hot."

    return ("I can answer questions about your BMI, fitness score, weight goals, "
            "sleep, hydration, steps, and predicted health risks. Try asking, "
            "e.g., \"Will I be able to reach my weight goal in 3 months?\"")


def _openai_answer(question: str, context: dict, api_key: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        system_prompt = (
            "You are the AI assistant inside a Health & Fitness Digital Twin app. "
            "Answer briefly and personally using the user's data below. Always "
            "remind the user this is not medical advice when discussing health risks.\n\n"
            + _build_context_string(context)
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(AI service unavailable, falling back to built-in assistant)\n\n" + \
            _rule_based_answer(question, context)


def get_chatbot_response(question: str, context: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return _openai_answer(question, context, api_key)
    return _rule_based_answer(question, context)
