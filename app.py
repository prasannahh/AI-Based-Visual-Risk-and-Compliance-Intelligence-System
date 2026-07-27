"""
app.py
------
Health & Fitness Digital Twin -- main Streamlit application.

Run with:
    streamlit run app.py

Pages (mirrors the 6 modules from the project plan):
    1. Login / Register           -> Module 1: User Profile
    2. Profile & Daily Log        -> Module 1 & 2
    3. AI Predictions             -> Module 3
    4. Digital Twin Simulation    -> Module 4
    5. Recommendations            -> Module 5
    6. Dashboard                  -> Module 6
    + AI Assistant (chatbot)
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select, func

from database import init_db, get_session, User, DailyLog, Prediction, Simulation, Recommendation
from ml.bmi import calculate_bmi, bmi_category, calculate_bmr, calculate_tdee
from ml.weight_predictor import predict_weight_change
from ml.fitness_score import calculate_fitness_score
from ml.risk_classifier import predict_risks
from ml import kaggle_models
from simulation import run_simulation, compare_scenarios
from recommendations import generate_recommendations
from chatbot import get_chatbot_response
from utils import hash_password, verify_password
from style import inject_custom_css, hero_header, render_footer, risk_badge

st.set_page_config(page_title="Health & Fitness Digital Twin", page_icon="🩺", layout="wide")
inject_custom_css()

# ---------------------------------------------------------------------------
# DB init (safe to call every run -- CREATE TABLE IF NOT EXISTS style)
# ---------------------------------------------------------------------------
try:
    init_db()
except Exception as e:
    st.error(
        "❌ Could not connect to PostgreSQL. Please check your `.env` file and "
        "make sure PostgreSQL is running. See README.md for setup steps.\n\n"
        f"Details: {e}"
    )
    st.stop()

if "user_id" not in st.session_state:
    st.session_state.user_id = None


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------
SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What was your first school's name?",
    "What is your favorite food?",
]


def login_register_screen():
    hero_header(
        "🩺 Health & Fitness Digital Twin",
        "An AI-powered virtual model of your health — predict, simulate, and improve.",
    )

    tab_login, tab_register, tab_forgot = st.tabs(["🔑 Log In", "📝 Register", "❓ Forgot Password"])

    # ---------------- LOG IN ----------------
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with get_session() as session:
                    user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
                if user and verify_password(password, user.password_hash):
                    st.session_state.user_id = user.user_id
                    st.success(f"Welcome back, {user.name.split(' ')[0]}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password. Please try again.")

    # ---------------- REGISTER ----------------
    with tab_register:
        with st.form("register_form"):
            st.markdown("**Account details**")
            name = st.text_input("Full name")
            email = st.text_input("Email", key="reg_email")
            c1, c2 = st.columns(2)
            with c1:
                password = st.text_input("Password", type="password", key="reg_pw")
            with c2:
                confirm_password = st.text_input("Confirm password", type="password", key="reg_pw2")

            st.markdown("**Profile**")
            c3, c4 = st.columns(2)
            with c3:
                age = st.number_input("Age", 10, 100, 25)
                height_cm = st.number_input("Height (cm)", 100.0, 250.0, 170.0)
            with c4:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                weight_kg = st.number_input("Weight (kg)", 30.0, 250.0, 70.0)
            blood_group = st.selectbox(
                "Blood group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
            )
            fitness_goal = st.selectbox(
                "Fitness goal", ["weight_loss", "muscle_gain", "endurance", "maintenance"]
            )
            medical_history = st.text_area("Medical history / allergies (optional)")

            st.markdown("**Account recovery** (used for Forgot Password)")
            c5, c6 = st.columns(2)
            with c5:
                security_question = st.selectbox("Security question", SECURITY_QUESTIONS)
            with c6:
                security_answer = st.text_input("Your answer")

            submitted = st.form_submit_button("Create account")

        if submitted:
            if not name or not email or not password:
                st.error("Name, email, and password are required.")
            elif password != confirm_password:
                st.error("Passwords don't match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif not security_answer:
                st.error("Please answer the security question (needed for password recovery).")
            else:
                with get_session() as session:
                    existing = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
                    if existing:
                        st.error("An account with that email already exists.")
                    else:
                        new_user = User(
                            name=name, email=email, password_hash=hash_password(password),
                            age=int(age), gender=gender, height_cm=height_cm, weight_kg=weight_kg,
                            blood_group=blood_group, fitness_goal=fitness_goal,
                            medical_history=medical_history,
                            security_question=security_question,
                            security_answer_hash=hash_password(security_answer.strip().lower()),
                        )
                        session.add(new_user)
                        session.commit()
                        st.success("🎉 Account created! Please log in from the 'Log In' tab.")

    # ---------------- FORGOT PASSWORD ----------------
    with tab_forgot:
        st.caption("Verify your identity with your security question, then set a new password.")

        if "forgot_pw_stage" not in st.session_state:
            st.session_state.forgot_pw_stage = "lookup"
            st.session_state.forgot_pw_user_id = None

        if st.session_state.forgot_pw_stage == "lookup":
            with st.form("forgot_lookup_form"):
                fp_email = st.text_input("Your account email")
                lookup_submitted = st.form_submit_button("Continue")
            if lookup_submitted:
                with get_session() as session:
                    user = session.execute(select(User).where(User.email == fp_email)).scalar_one_or_none()
                if user is None:
                    st.error("No account found with that email.")
                else:
                    st.session_state.forgot_pw_stage = "verify"
                    st.session_state.forgot_pw_user_id = user.user_id
                    st.session_state.forgot_pw_question = user.security_question
                    st.rerun()

        elif st.session_state.forgot_pw_stage == "verify":
            st.info(f"Security question: **{st.session_state.forgot_pw_question}**")
            with st.form("forgot_verify_form"):
                answer = st.text_input("Your answer")
                new_password = st.text_input("New password", type="password")
                confirm_new_password = st.text_input("Confirm new password", type="password")
                c1, c2 = st.columns(2)
                with c1:
                    verify_submitted = st.form_submit_button("Reset Password")
                with c2:
                    cancel = st.form_submit_button("Cancel")

            if cancel:
                st.session_state.forgot_pw_stage = "lookup"
                st.session_state.forgot_pw_user_id = None
                st.rerun()

            if verify_submitted:
                if new_password != confirm_new_password:
                    st.error("New passwords don't match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with get_session() as session:
                        user = get_user(session, st.session_state.forgot_pw_user_id)
                        if not verify_password(answer.strip().lower(), user.security_answer_hash):
                            st.error("❌ That answer doesn't match our records.")
                        else:
                            user.password_hash = hash_password(new_password)
                            session.commit()
                            st.success("✅ Password reset! You can now log in with your new password.")
                            st.session_state.forgot_pw_stage = "lookup"
                            st.session_state.forgot_pw_user_id = None

    render_footer()


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
def get_user(session, user_id):
    return session.get(User, user_id)


def get_recent_logs(session, user_id, days=7):
    since = date.today() - timedelta(days=days)
    stmt = (
        select(DailyLog)
        .where(DailyLog.user_id == user_id, DailyLog.log_date >= since)
        .order_by(DailyLog.log_date)
    )
    return session.execute(stmt).scalars().all()


def compute_averages(logs):
    if not logs:
        return None
    n = len(logs)
    return {
        "steps": sum(l.steps or 0 for l in logs) / n,
        "sleep_hours": sum(l.sleep_hours or 0 for l in logs) / n,
        "exercise_minutes": sum(l.exercise_minutes or 0 for l in logs) / n,
        "water_liters": sum(l.water_liters or 0 for l in logs) / n,
        "calories_consumed": sum(l.calories_consumed or 0 for l in logs) / n,
    }


# ---------------------------------------------------------------------------
# Page: Profile & Daily Log
# ---------------------------------------------------------------------------
def page_profile_and_log(user):
    st.header("👤 Profile & Daily Health Log")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Profile")
        st.write(f"**Name:** {user.name}")
        st.write(f"**Age:** {user.age}  |  **Gender:** {user.gender}")
        st.write(f"**Height:** {user.height_cm} cm  |  **Weight:** {user.weight_kg} kg")
        st.write(f"**Blood group:** {user.blood_group}")
        st.write(f"**Goal:** {user.fitness_goal.replace('_', ' ').title()}")
        if user.medical_history:
            st.write(f"**Medical history:** {user.medical_history}")

        with st.expander("Update weight / goal"):
            with st.form("update_profile"):
                new_weight = st.number_input("Current weight (kg)", 30.0, 250.0, float(user.weight_kg))
                new_goal = st.selectbox(
                    "Fitness goal", ["weight_loss", "muscle_gain", "endurance", "maintenance"],
                    index=["weight_loss", "muscle_gain", "endurance", "maintenance"].index(user.fitness_goal)
                    if user.fitness_goal in ["weight_loss", "muscle_gain", "endurance", "maintenance"] else 0,
                )
                if st.form_submit_button("Save"):
                    with get_session() as session:
                        db_user = get_user(session, user.user_id)
                        db_user.weight_kg = new_weight
                        db_user.fitness_goal = new_goal
                        session.commit()
                    st.success("Profile updated.")
                    st.rerun()

    with col2:
        st.subheader("Log Today's Health Data")
        with st.form("daily_log_form"):
            log_date = st.date_input("Date", value=date.today())
            steps = st.number_input("Steps walked", 0, 60000, 5000, step=500)
            exercise_minutes = st.number_input("Exercise duration (min)", 0, 400, 20, step=5)
            calories_burned = st.number_input("Calories burned (exercise)", 0.0, 3000.0, 200.0, step=50.0)
            calories_consumed = st.number_input("Calories consumed", 0.0, 6000.0, 2200.0, step=50.0)
            water_liters = st.number_input("Water intake (L)", 0.0, 10.0, 2.0, step=0.1)
            sleep_hours = st.number_input("Sleep hours", 0.0, 14.0, 7.0, step=0.5)
            sleep_quality = st.selectbox("Sleep quality", ["poor", "average", "good", "excellent"], index=1)
            weight_kg = st.number_input("Weight today (kg, optional)", 0.0, 250.0, float(user.weight_kg))

            with st.expander("Optional vitals"):
                heart_rate = st.number_input("Resting heart rate (bpm)", 0, 220, 70)
                bp_sys = st.number_input("Blood pressure (systolic)", 0, 250, 120)
                bp_dia = st.number_input("Blood pressure (diastolic)", 0, 200, 80)
                blood_sugar = st.number_input("Blood sugar (mg/dL)", 0.0, 500.0, 95.0)

            submitted = st.form_submit_button("Save entry")

        if submitted:
            with get_session() as session:
                entry = DailyLog(
                    user_id=user.user_id, log_date=log_date, steps=steps,
                    exercise_minutes=exercise_minutes, calories_burned=calories_burned,
                    calories_consumed=calories_consumed, water_liters=water_liters,
                    sleep_hours=sleep_hours, sleep_quality=sleep_quality,
                    weight_kg=weight_kg or None, heart_rate=heart_rate or None,
                    blood_pressure_sys=bp_sys or None, blood_pressure_dia=bp_dia or None,
                    blood_sugar=blood_sugar or None,
                )
                session.add(entry)
                if weight_kg:
                    db_user = get_user(session, user.user_id)
                    db_user.weight_kg = weight_kg
                session.commit()
            st.success(f"Saved entry for {log_date}.")
            st.rerun()


# ---------------------------------------------------------------------------
# Page: AI Predictions
# ---------------------------------------------------------------------------
def page_predictions(user):
    st.header("🔮 AI Predictions")
    st.caption("Predictions use your last 7 days of logged data. Log data first if you see a warning below.")

    with get_session() as session:
        logs = get_recent_logs(session, user.user_id, days=7)
    averages = compute_averages(logs)

    if not averages:
        st.warning("No recent daily logs found. Go to **Profile & Daily Log** to add your first entry.")
        return

    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee = calculate_tdee(bmr, averages["steps"])
    calorie_balance = averages["calories_consumed"] - tdee
    bmi = calculate_bmi(user.weight_kg, user.height_cm)

    horizon = st.slider("Prediction horizon (days)", 7, 180, 30)

    weight_change = predict_weight_change(
        current_weight_kg=user.weight_kg, height_cm=user.height_cm, age=user.age,
        gender=user.gender, avg_daily_calorie_balance=calorie_balance,
        avg_sleep_hours=averages["sleep_hours"], avg_steps=averages["steps"], horizon_days=horizon,
    )
    projected_weight = round(user.weight_kg + weight_change, 2)
    projected_bmi = calculate_bmi(projected_weight, user.height_cm)

    fitness_score = calculate_fitness_score(
        steps=averages["steps"], sleep_hours=averages["sleep_hours"],
        exercise_minutes=averages["exercise_minutes"], water_liters=averages["water_liters"],
        calories_consumed=averages["calories_consumed"], tdee=tdee, fitness_goal=user.fitness_goal,
    )

    risks = predict_risks(
        bmi=bmi, age=user.age, avg_steps=averages["steps"], avg_sleep_hours=averages["sleep_hours"],
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current BMI", f"{bmi}", bmi_category(bmi))
    c2.metric(f"Projected weight ({horizon}d)", f"{projected_weight} kg", f"{weight_change:+.1f} kg")
    c3.metric("Fitness Score", f"{fitness_score}/100")
    c4.metric("Daily TDEE", f"{int(tdee)} kcal")

    st.subheader("Predicted Health Risks")
    st.caption("⚠️ Educational estimate only -- not a medical diagnosis.")
    rc1, rc2, rc3 = st.columns(3)
    for col, (name, info) in zip([rc1, rc2, rc3], risks.items()):
        col.metric(name.title() + " risk", info["level"], f"{int(info['probability']*100)}% conf.")

    # --- Kaggle-trained real-data models (Module: multi-dataset ML evaluation) ---
    availability = kaggle_models.which_kaggle_models_available()
    if any(availability.values()):
        st.divider()
        st.subheader("📊 Real-Dataset Model Predictions")
        st.caption(
            "These predictions come from models trained on real Kaggle datasets "
            "(see data/README.md), not synthetic data."
        )
        kcols = st.columns(4)

        if availability["obesity"]:
            result = kaggle_models.predict_obesity_level({
                "age": user.age, "height_m": user.height_cm / 100, "weight_kg": user.weight_kg,
                "gender": user.gender, "faf": min(3, averages["exercise_minutes"] / 30),
                "ch2o": min(3, averages["water_liters"]),
            })
            with kcols[0]:
                st.markdown("**Obesity Level**")
                st.markdown(f"*(RandomForestClassifier)*")
                st.write(f"**{result['level'].replace('_', ' ')}**")
                st.caption(f"{int(result['confidence']*100)}% model confidence")

        if availability["diabetes"]:
            result = kaggle_models.predict_diabetes_risk({
                "age": user.age, "bmi": bmi, "gender": user.gender,
                "blood_glucose": logs[-1].blood_sugar if logs[-1].blood_sugar else 100,
                "hypertension": 1 if (logs[-1].blood_pressure_sys or 0) >= 140 else 0,
            })
            with kcols[1]:
                st.markdown("**Diabetes Risk**")
                st.markdown(f"*(LogisticRegression)*")
                st.markdown(f"**{result['level']}** {risk_badge(result['level'])}", unsafe_allow_html=True)
                st.caption(f"{int(result['probability']*100)}% probability")

        if availability["sleep"]:
            result = kaggle_models.predict_sleep_disorder({
                "age": user.age, "sleep_hours": averages["sleep_hours"], "gender": user.gender,
                "exercise_minutes": averages["exercise_minutes"], "heart_rate": logs[-1].heart_rate or 72,
                "steps": averages["steps"], "bmi_category": bmi_category(bmi),
            })
            with kcols[2]:
                st.markdown("**Sleep Disorder**")
                st.markdown(f"*(KNeighborsClassifier)*")
                st.write(f"**{result['disorder']}**")
                st.caption(f"{int(result['confidence']*100)}% model confidence")

        if availability["calories"]:
            result = kaggle_models.predict_calories_burnt({
                "age": user.age, "height_cm": user.height_cm, "weight_kg": user.weight_kg,
                "duration_minutes": max(10, averages["exercise_minutes"]), "gender": user.gender,
            })
            with kcols[3]:
                st.markdown("**Calories Burnt / session**")
                st.markdown(f"*(GradientBoostingRegressor)*")
                st.write(f"**{result} kcal**")
                st.caption(f"for a ~{int(max(10, averages['exercise_minutes']))} min workout")

        missing = [k for k, v in availability.items() if not v]
        if missing:
            st.info(
                f"Add the remaining dataset(s) ({', '.join(missing)}) to `data/` and run "
                f"`python -m ml.train_kaggle_models` to unlock all 4 real-data models. "
                f"See `data/README.md`."
            )
    else:
        st.info(
            "💡 Want predictions from models trained on **real Kaggle datasets** instead of "
            "synthetic data? See `data/README.md` for download links, then run "
            "`python -m ml.train_kaggle_models`."
        )

    if st.button("💾 Save this prediction snapshot"):
        with get_session() as session:
            pred = Prediction(
                user_id=user.user_id, predicted_weight_kg=projected_weight, predicted_bmi=projected_bmi,
                fitness_score=fitness_score, daily_calorie_requirement=tdee,
                obesity_risk=risks["obesity"]["level"], diabetes_risk=risks["diabetes"]["level"],
                hypertension_risk=risks["hypertension"]["level"],
            )
            session.add(pred)
            session.commit()
        st.success("Prediction saved to your history.")

    # Store latest for other pages / chatbot context
    st.session_state.latest_prediction = {
        "bmi": bmi, "fitness_score": fitness_score, "predicted_weight_30d": projected_weight,
        "risks": risks, "tdee": tdee,
    }


# ---------------------------------------------------------------------------
# Page: Digital Twin Simulation
# ---------------------------------------------------------------------------
def page_simulation(user):
    st.header("🧪 Digital Twin Simulation")
    st.caption('Run "what-if" scenarios to see how lifestyle changes affect your future health.')

    st.subheader("Scenario: Improved Lifestyle")
    col1, col2, col3 = st.columns(3)
    with col1:
        sim_steps = st.number_input("Steps/day", 0, 60000, 10000, step=500)
        sim_sleep = st.number_input("Sleep hours/night", 0.0, 14.0, 8.0, step=0.5)
    with col2:
        sim_calories = st.number_input("Calories consumed/day", 0.0, 6000.0, 2000.0, step=50.0)
        sim_exercise = st.number_input("Exercise minutes/day", 0, 400, 45, step=5)
    with col3:
        sim_water = st.number_input("Water (L)/day", 0.0, 10.0, 2.5, step=0.1)
        horizon = st.number_input("Horizon (days)", 7, 365, 30, step=1)

    if st.button("▶️ Run Simulation"):
        # "Current path" baseline: use logged 7-day averages if available, else profile-only.
        with get_session() as session:
            logs = get_recent_logs(session, user.user_id, days=7)
        averages = compute_averages(logs) or {
            "steps": 5000, "sleep_hours": 6.5, "exercise_minutes": 15,
            "water_liters": 1.5, "calories_consumed": user.weight_kg * 30,
        }

        base = run_simulation(
            current_weight_kg=user.weight_kg, height_cm=user.height_cm, age=user.age,
            gender=user.gender, fitness_goal=user.fitness_goal, horizon_days=horizon,
            sim_steps=averages["steps"], sim_sleep_hours=averages["sleep_hours"],
            sim_calories_consumed=averages["calories_consumed"],
            sim_exercise_minutes=averages["exercise_minutes"], sim_water_liters=averages["water_liters"],
        )
        improved = run_simulation(
            current_weight_kg=user.weight_kg, height_cm=user.height_cm, age=user.age,
            gender=user.gender, fitness_goal=user.fitness_goal, horizon_days=horizon,
            sim_steps=sim_steps, sim_sleep_hours=sim_sleep, sim_calories_consumed=sim_calories,
            sim_exercise_minutes=sim_exercise, sim_water_liters=sim_water,
        )
        comparison = compare_scenarios(base, improved)

        st.subheader("Results")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**📉 Current Path**")
            st.metric("Projected weight", f"{base['projected_weight_kg']} kg")
            st.metric("Fitness score", f"{base['fitness_score']}/100")
            st.metric("BMI", f"{base['projected_bmi']}")
        with colB:
            st.markdown("**✅ Improved Lifestyle**")
            st.metric("Projected weight", f"{improved['projected_weight_kg']} kg",
                       f"{improved['projected_weight_kg'] - base['projected_weight_kg']:+.1f} kg")
            st.metric("Fitness score", f"{improved['fitness_score']}/100",
                       f"{comparison['fitness_score_gain']:+.1f}")
            st.metric("BMI", f"{improved['projected_bmi']}")

        # Simple trajectory chart (linear interpolation for visualization only)
        days = list(range(0, horizon + 1, max(1, horizon // 20)))
        base_traj = [user.weight_kg + (base["weight_change_kg"] * d / horizon) for d in days]
        improved_traj = [user.weight_kg + (improved["weight_change_kg"] * d / horizon) for d in days]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=base_traj, mode="lines+markers", name="Current path"))
        fig.add_trace(go.Scatter(x=days, y=improved_traj, mode="lines+markers", name="Improved lifestyle"))
        fig.update_layout(title="Projected Weight Trajectory", xaxis_title="Days", yaxis_title="Weight (kg)")
        st.plotly_chart(fig, use_container_width=True)

        st.info(
            f"By switching to the improved lifestyle, the Digital Twin projects a "
            f"**{abs(comparison['weight_swing_kg'])} kg** difference in weight and a "
            f"**{comparison['fitness_score_gain']:+.1f} point** change in fitness score "
            f"over {horizon} days."
        )

        with get_session() as session:
            session.add(Simulation(
                user_id=user.user_id, scenario_name="Improved lifestyle vs current path",
                horizon_days=horizon,
                input_params={"steps": sim_steps, "sleep": sim_sleep, "calories": sim_calories,
                               "exercise": sim_exercise, "water": sim_water},
                projected_weight_kg=improved["projected_weight_kg"],
                projected_bmi=improved["projected_bmi"],
                projected_fitness_score=improved["fitness_score"],
                summary=f"Weight swing: {comparison['weight_swing_kg']}kg, "
                        f"Fitness gain: {comparison['fitness_score_gain']}",
            ))
            session.commit()


# ---------------------------------------------------------------------------
# Page: Recommendations
# ---------------------------------------------------------------------------
def page_recommendations(user):
    st.header("💡 Personalized Recommendations")

    with get_session() as session:
        logs = get_recent_logs(session, user.user_id, days=7)
    averages = compute_averages(logs)

    if not averages:
        st.warning("No recent daily logs found. Add entries in **Profile & Daily Log** first.")
        return

    bmr = calculate_bmr(user.weight_kg, user.height_cm, user.age, user.gender)
    tdee = calculate_tdee(bmr, averages["steps"])
    calorie_balance = averages["calories_consumed"] - tdee
    bmi = calculate_bmi(user.weight_kg, user.height_cm)
    risks = predict_risks(bmi=bmi, age=user.age, avg_steps=averages["steps"],
                           avg_sleep_hours=averages["sleep_hours"])

    recs = generate_recommendations(
        avg_steps=averages["steps"], avg_sleep_hours=averages["sleep_hours"],
        avg_water_liters=averages["water_liters"], avg_exercise_minutes=averages["exercise_minutes"],
        calorie_balance=calorie_balance, fitness_goal=user.fitness_goal, risks=risks,
    )

    priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    for rec in sorted(recs, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["priority"]]):
        st.markdown(f"{priority_color[rec['priority']]} **[{rec['category'].title()}]** {rec['text']}")

    if st.button("💾 Save these recommendations"):
        with get_session() as session:
            for rec in recs:
                session.add(Recommendation(
                    user_id=user.user_id, category=rec["category"],
                    priority=rec["priority"], recommendation_text=rec["text"],
                ))
            session.commit()
        st.success("Saved to your recommendation history.")


# ---------------------------------------------------------------------------
# Page: Dashboard
# ---------------------------------------------------------------------------
def page_dashboard(user):
    st.header("📊 Interactive Dashboard")

    with get_session() as session:
        logs = session.execute(
            select(DailyLog).where(DailyLog.user_id == user.user_id).order_by(DailyLog.log_date)
        ).scalars().all()

    if not logs:
        st.warning("No data logged yet. Add entries in **Profile & Daily Log** first.")
        return

    df = pd.DataFrame([{
        "date": l.log_date, "steps": l.steps, "sleep_hours": l.sleep_hours,
        "weight_kg": l.weight_kg, "calories_consumed": l.calories_consumed,
        "calories_burned": l.calories_burned, "water_liters": l.water_liters,
        "heart_rate": l.heart_rate,
    } for l in logs])

    c1, c2 = st.columns(2)
    with c1:
        fig_weight = go.Figure()
        fig_weight.add_trace(go.Scatter(x=df["date"], y=df["weight_kg"], mode="lines+markers", name="Weight"))
        fig_weight.update_layout(title="Weight Over Time (kg)")
        st.plotly_chart(fig_weight, use_container_width=True)

        fig_sleep = go.Figure()
        fig_sleep.add_trace(go.Bar(x=df["date"], y=df["sleep_hours"], name="Sleep hours"))
        fig_sleep.update_layout(title="Sleep Hours per Day")
        st.plotly_chart(fig_sleep, use_container_width=True)

    with c2:
        fig_steps = go.Figure()
        fig_steps.add_trace(go.Bar(x=df["date"], y=df["steps"], name="Steps"))
        fig_steps.update_layout(title="Steps per Day")
        st.plotly_chart(fig_steps, use_container_width=True)

        fig_cal = go.Figure()
        fig_cal.add_trace(go.Scatter(x=df["date"], y=df["calories_consumed"], mode="lines", name="Consumed"))
        fig_cal.add_trace(go.Scatter(x=df["date"], y=df["calories_burned"], mode="lines", name="Burned (exercise)"))
        fig_cal.update_layout(title="Calories: Consumed vs Burned")
        st.plotly_chart(fig_cal, use_container_width=True)

    st.subheader("Weekly Summary")
    recent = df.tail(7)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Avg steps", f"{recent['steps'].mean():.0f}")
    s2.metric("Avg sleep", f"{recent['sleep_hours'].mean():.1f} h")
    s3.metric("Avg water", f"{compute_averages(logs[-7:])['water_liters']:.1f} L")
    s4.metric("Entries logged", f"{len(df)}")

    with st.expander("📜 Raw log history"):
        st.dataframe(df, use_container_width=True)

    with get_session() as session:
        pred_history = session.execute(
            select(Prediction).where(Prediction.user_id == user.user_id).order_by(Prediction.created_at)
        ).scalars().all()
    if pred_history:
        st.subheader("Prediction History")
        pdf = pd.DataFrame([{
            "date": p.created_at, "predicted_weight": p.predicted_weight_kg,
            "fitness_score": p.fitness_score, "bmi": p.predicted_bmi,
        } for p in pred_history])
        st.dataframe(pdf, use_container_width=True)


# ---------------------------------------------------------------------------
# Page: AI Assistant (chatbot)
# ---------------------------------------------------------------------------
def page_chatbot(user):
    st.header("🤖 AI Health Assistant")
    st.caption("Ask about your BMI, fitness score, predictions, or general health guidance.")

    context = st.session_state.get("latest_prediction", {})
    context.update({
        "age": user.age, "gender": user.gender, "height_cm": user.height_cm,
        "weight_kg": user.weight_kg, "fitness_goal": user.fitness_goal,
    })

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("Ask your Digital Twin something, e.g. 'Will I reach my weight goal in 3 months?'")
    if question:
        st.session_state.chat_history.append(("user", question))
        answer = get_chatbot_response(question, context)
        st.session_state.chat_history.append(("assistant", answer))
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if st.session_state.user_id is None:
        login_register_screen()
        return

    with get_session() as session:
        user = get_user(session, st.session_state.user_id)

    if user is None:
        st.session_state.user_id = None
        st.rerun()
        return

    st.sidebar.markdown(f"### 👋 Hi, {user.name.split(' ')[0]}")
    st.sidebar.caption(user.email)
    page = st.sidebar.radio(
        "Navigate",
        ["Profile & Daily Log", "AI Predictions", "Digital Twin Simulation",
         "Recommendations", "Dashboard", "AI Assistant"],
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log out"):
        st.session_state.user_id = None
        st.session_state.pop("chat_history", None)
        st.rerun()

    pages = {
        "Profile & Daily Log": page_profile_and_log,
        "AI Predictions": page_predictions,
        "Digital Twin Simulation": page_simulation,
        "Recommendations": page_recommendations,
        "Dashboard": page_dashboard,
        "AI Assistant": page_chatbot,
    }
    hero_header("Health & Fitness Digital Twin", page)
    pages[page](user)
    render_footer()


if __name__ == "__main__":
    main()