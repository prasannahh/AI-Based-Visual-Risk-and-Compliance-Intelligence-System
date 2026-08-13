"""
pages_app/profile.py
Milestone 1: Data Collection & User Profiling.
Avatar & summary, Goals card, Add New Data form, Today's Schedule editor,
Behavioral Patterns widget.
"""

from datetime import date, time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_bridge  # noqa: F401  (links the Milestone 2 AI Core Layer)

import database as db
from ai_models.common import streamlit_ui as ui
from ai_models.health import predict as health_ai
from ui_components import render_avatar_block
from utils import flash, render_flash, trend_html


def render():
    render_flash()

    user_id = st.session_state.user_id
    user = db.get_user(user_id)
    goals = db.get_goals(user_id)
    days_active = db.get_days_active(user_id)

    goal_score = 0.0
    if not goals.empty:
        goals["pct"] = (goals["current_progress"].astype(float) / goals["target_amount"].astype(float)).clip(0, 1) * 100
        goal_score = goals["pct"].mean()

    with st.container(border=True):
        render_avatar_block(user, days_active, goal_score)

    col_left, col_right = st.columns([1, 1])

    # --------------------------- Goals card --------------------------- #
    with col_left:
        with st.container(border=True):
            st.markdown("#### 🎯 My Goals")
            if goals.empty:
                st.caption("No goals yet — add one below.")
            else:
                for _, g in goals.iterrows():
                    pct = min(float(g["current_progress"]) / float(g["target_amount"]) * 100, 100) if g["target_amount"] else 0
                    st.markdown(f"**{g['goal_name']}**")
                    st.progress(min(pct / 100, 1.0), text=f"{g['current_progress']:.0f} / {g['target_amount']:.0f} ({pct:.0f}%)")
                    with st.expander(f"Edit '{g['goal_name']}'"):
                        new_val = st.number_input(
                            "Current progress",
                            min_value=0.0,
                            value=float(g["current_progress"]),
                            key=f"goal_progress_{g['goal_id']}",
                        )
                        c1, c2 = st.columns(2)
                        if c1.button("Save", key=f"save_goal_{g['goal_id']}", width='stretch'):
                            db.update_goal_progress(g["goal_id"], new_val)
                            flash("Goal updated.")
                            st.rerun()
                        if c2.button("Delete", key=f"del_goal_{g['goal_id']}", width='stretch'):
                            db.delete_goal(g["goal_id"])
                            flash("Goal deleted.", "info")
                            st.rerun()

            with st.expander("➕ Add a new goal"):
                with st.form("add_goal_form"):
                    gname = st.text_input("Goal name (e.g., Emergency Fund)")
                    gtarget = st.number_input("Target amount", min_value=0.0, value=1000.0)
                    gcurrent = st.number_input("Current progress", min_value=0.0, value=0.0)
                    gdate = st.date_input("Target date", value=date.today())
                    if st.form_submit_button("Add Goal", width='stretch'):
                        if gname:
                            db.add_goal(user_id, gname, gtarget, gcurrent, gdate)
                            flash("Goal added.")
                            st.rerun()
                        else:
                            flash("Please name your goal.", "error")

    # ----------------------- Behavioral patterns ----------------------- #
    with col_right:
        with st.container(border=True):
            st.markdown("#### 📊 Behavioral Patterns")
            patterns = db.compute_behavioral_patterns(user_id, date.today())
            if days_active <= 1:
                st.caption("First day logged — showing today's activity only. Trends unlock from day 2.")
            html = "".join(trend_html(k, v["value"], v["trend_pct"]) for k, v in patterns.items())
            st.markdown(html, unsafe_allow_html=True)

    # --------------------------- Add New Data --------------------------- #
    with st.container(border=True):
        st.markdown("#### ➕ Add New Data")
        entry_type = st.radio("Category", ["Finance", "Study", "Habits"], horizontal=True, key="entry_type")

        if entry_type == "Finance":
            with st.form("finance_form"):
                c1, c2 = st.columns(2)
                category = c1.selectbox("Category", ["Housing", "Food", "Dining Out", "Transport", "Salary", "Investment", "Entertainment", "Other"])
                ttype = c2.selectbox("Transaction Type", ["Income", "Expense", "Savings"])
                amount = st.number_input("Amount", min_value=0.0, value=0.0)
                fdate = st.date_input("Date", value=date.today(), key="fin_date")
                if st.form_submit_button("Save Entry", width='stretch'):
                    db.add_financial_record(user_id, category, amount, ttype, fdate)
                    flash("Financial record saved.")
                    st.rerun()

        elif entry_type == "Study":
            with st.form("study_form"):
                subject = st.text_input("Subject")
                c1, c2 = st.columns(2)
                hours = c1.number_input("Hours logged", min_value=0.0, value=1.0, step=0.5)
                score = c2.number_input("Performance score (0-100)", min_value=0.0, max_value=100.0, value=75.0)
                sdate = st.date_input("Date", value=date.today(), key="study_date")
                if st.form_submit_button("Save Entry", width='stretch'):
                    if subject:
                        db.add_study_activity(user_id, subject, hours, score, sdate)
                        flash("Study activity saved.")
                        st.rerun()
                    else:
                        flash("Please enter a subject.", "error")

        else:  # Habits
            with st.form("habit_form"):
                habit_name = st.selectbox(
                    "Habit",
                    ["Exercise Frequency", "Sleep Schedule", "Reading Habit", "Meal Prep", "Custom"],
                )
                if habit_name == "Custom":
                    habit_name = st.text_input("Custom habit name")
                c1, c2 = st.columns(2)
                status = c1.selectbox("Status", ["Done", "Partial", "Missed"])
                completion = c2.slider("Completion rate (%)", 0, 100, 70)
                hdate = st.date_input("Date", value=date.today(), key="habit_date")
                if st.form_submit_button("Save Entry", width='stretch'):
                    if habit_name:
                        db.add_habit(user_id, habit_name, status, completion, hdate)
                        flash("Habit entry saved.")
                        st.rerun()
                    else:
                        flash("Please name the habit.", "error")

    # ------------------------- Today's Schedule ------------------------- #
    with st.container(border=True):
        st.markdown("#### 🗓️ Today's Schedule")
        today_sched = db.get_schedule(user_id, date.today())
        if today_sched.empty:
            editor_df = pd.DataFrame(
                [{"activity_name": "", "planned_time": None, "actual_time": None, "status": "Upcoming"}]
            )
        else:
            editor_df = today_sched[["activity_name", "planned_time", "actual_time", "status"]]

        edited = st.data_editor(
            editor_df,
            num_rows="dynamic",
            width='stretch',
            column_config={
                "activity_name": st.column_config.TextColumn("Activity", required=True),
                "planned_time": st.column_config.TimeColumn("Planned Time"),
                "actual_time": st.column_config.TimeColumn("Actual Time"),
                "status": st.column_config.SelectboxColumn("Status", options=["Upcoming", "In Progress", "Completed", "Missed"]),
            },
            key="schedule_editor",
        )
        if st.button("💾 Save Schedule", key="save_schedule"):
            rows = edited.to_dict("records")
            db.replace_schedule(user_id, date.today(), rows)
            flash("Schedule saved.")
            st.rerun()

    # ------------------------- Today's Checklist ------------------------- #
    with st.container(border=True):
        st.markdown("#### ✅ Today's Checklist")
        checklist_tasks = db.get_schedule(user_id, date.today())
        if checklist_tasks.empty:
            st.caption("No tasks scheduled for today yet — add some in Today's Schedule above.")
        else:
            all_done = True
            for _, row in checklist_tasks.iterrows():
                was_done = row["status"] == "Completed"
                checked = st.checkbox(
                    row["activity_name"],
                    value=was_done,
                    key=f"sched_done_{row['schedule_id']}",
                )
                if checked != was_done:
                    db.update_schedule_status(
                        int(row["schedule_id"]), "Completed" if checked else "Upcoming"
                    )
                    st.rerun()
                if not checked:
                    all_done = False

            if all_done:
                st.success("🎉 Great job! You've completed all of today's scheduled activities.")
                st.balloons()

    # ----------------------- AI Core (Milestone 2) ----------------------- #
    with st.container(border=True):
        st.markdown("#### 🔬 AI Health Assistant")
        ai_tab = st.tabs(["BMI Assessment", "Weight Prediction", "Calorie Prediction", "Health Risk", "Model Status"])

        gender = (st.session_state.user_gender or "Male").lower()
        age = int(user.get("age") or 25) if user.get("age") else 25
        last_health = db.get_latest_health(user_id)
        height_default = float(last_health["height_cm"]) if last_health.get("height_cm") else 170.0
        weight_default = float(last_health["weight_kg"]) if last_health.get("weight_kg") else 70.0

        # Widget keys whose values feed height/weight into the prediction tabs.
        # Clearing them (on save + rerun) lets the freshly saved height/weight
        # become the default shown in every prediction tab below.
        _health_widget_keys = [
            "health_height", "health_weight",
            "health_w_height", "health_w_weight",
            "health_c_height", "health_c_weight",
            "health_r_height", "health_r_weight",
        ]

        def _use_saved_health(msg: str) -> None:
            for key in _health_widget_keys:
                if key in st.session_state:
                    del st.session_state[key]
            flash(msg)
            st.rerun()

        # ------------------------- BMI Assessment ------------------------- #
        with ai_tab[0]:
            st.markdown("**Assess your BMI and get health suggestions**")
            c1, c2 = st.columns(2)
            height = c1.number_input("Height (cm)", 120.0, 230.0, height_default, 0.1, key="health_height")
            weight = c2.number_input("Weight (kg)", 30.0, 250.0, weight_default, 0.1, key="health_weight")
            result = health_ai.assess_bmi(age, gender, height, weight)
            st.metric("BMI", f"{result['bmi']:.1f}", result["category"])
            st.markdown("**Suggestions**")
            for suggestion in result["suggestions"]:
                st.markdown(f"- {suggestion}")
            c_save, c_log = st.columns(2)
            if c_save.button("💾 Save health record", key="health_save"):
                ok = ui.safe_log("health record", db.add_health_record, user_id, date.today(), height, weight)
                if ok:
                    _use_saved_health("Health record saved — height & weight updated everywhere.")
                else:
                    flash("Could not save health record — check database connection.", "warning")
            if c_log.button("💾 Log assessment", key="health_bmi_log"):
                ui.safe_log(
                    "BMI assessment",
                    db.log_health_prediction,
                    user_id, "bmi", result["bmi"], result["category"], confidence=1.0,
                    input_data={"age": age, "gender": gender, "height_cm": height, "weight_kg": weight}, output_data=result,
                )
                flash("Assessment logged to your history.")

        # ----------------------- Weight Prediction ----------------------- #
        with ai_tab[1]:
            st.markdown("**Forecast your weight**")
            c1, c2, c3 = st.columns(3)
            w_age = c1.number_input("Age", 14, 100, age, key="health_w_age")
            w_weight = c2.number_input("Current weight (kg)", 30.0, 250.0, weight_default, 0.1, key="health_w_weight")
            w_height = c3.number_input("Height (cm)", 120.0, 230.0, height_default, 0.1, key="health_w_height")
            activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very_active"], index=2, key="health_w_activity")
            w_calories = st.number_input("Average daily calories", 800, 7000, 2400, 50, key="health_w_calories")
            days = st.slider("Forecast days", 7, 90, 30, key="health_w_days")
            forecast = health_ai.predict_weight_forecast(int(w_age), gender, w_height, w_weight, activity, int(w_calories), days=int(days))
            line = ui.figure(300)
            line.add_trace(go.Scatter(x=forecast["day"], y=forecast["predicted_weight_kg"], mode="lines+markers", line=dict(color=ui.ACCENT, width=3)))
            st.plotly_chart(line, width='stretch')
            st.metric("Projected weight", f"{forecast['predicted_weight_kg'].iloc[-1]:.1f} kg")
            if st.button("💾 Log prediction", key="health_w_log"):
                ui.safe_log(
                    "weight prediction",
                    db.log_health_prediction,
                    user_id, "weight_prediction",
                    float(forecast["predicted_weight_kg"].iloc[-1]), f"{days}-day forecast", confidence=1.0,
                    input_data={"age": w_age, "gender": gender, "height_cm": w_height, "weight_kg": w_weight, "activity_level": activity, "daily_calories": w_calories},
                    output_data=forecast.head(30).to_dict("records"),
                )
                flash("Prediction logged to your history.")

        # ---------------------- Calorie Prediction ---------------------- #
        with ai_tab[2]:
            st.markdown("**Predict your daily calorie requirement**")
            c1, c2 = st.columns(2)
            cal_weight = c1.number_input("Weight (kg)", 30.0, 250.0, weight_default, 0.1, key="health_c_weight")
            cal_height = c2.number_input("Height (cm)", 120.0, 230.0, height_default, 0.1, key="health_c_height")
            cal_activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very_active"], index=2, key="health_c_activity")
            result = health_ai.predict_calorie_requirement(age, gender, cal_height, cal_weight, cal_activity)
            ui.render_metrics(
                {"ML estimate": f"{result['ml_kcal']:,} kcal", "BMR": f"{result['mifflin_bmr_kcal']:,} kcal", "Maintenance": f"{result['maintenance_kcal']:,} kcal"},
                columns=3,
            )
            if st.button("💾 Log prediction", key="health_c_log"):
                ui.safe_log(
                    "calorie prediction",
                    db.log_health_prediction,
                    user_id, "calorie_prediction",
                    result["ml_kcal"], "Daily kcal", confidence=1.0,
                    input_data={"age": age, "gender": gender, "height_cm": cal_height, "weight_kg": cal_weight, "activity_level": cal_activity},
                    output_data=result,
                )
                flash("Prediction logged to your history.")

        # ------------------------- Health Risk ------------------------- #
        with ai_tab[3]:
            st.markdown("**Predict health-risk probabilities**")
            c1, c2 = st.columns(2)
            risk_weight = c1.number_input("Weight (kg)", 30.0, 250.0, weight_default, 0.1, key="health_r_weight")
            risk_height = c2.number_input("Height (cm)", 120.0, 230.0, height_default, 0.1, key="health_r_height")
            risk_activity = st.selectbox("Activity level", ["sedentary", "light", "moderate", "active", "very_active"], index=2, key="health_r_activity")
            risk_calories = st.number_input("Average daily calories", 800, 7000, 2400, 50, key="health_r_calories")
            risk_freq = st.slider("Exercise frequency (days/week)", 0, 7, 3, key="health_r_freq")
            risks = health_ai.predict_health_risks(int(age), gender, risk_height, risk_weight, risk_activity, int(risk_calories), int(risk_freq))
            for risk in risks:
                st.markdown(f"**{risk['disease']}** — {risk['probability_pct']:.0f}% ({risk['risk_level']} risk)")
                st.progress(min(risk["probability_pct"] / 100, 1.0))
                for rec in risk["recommendations"]:
                    st.markdown(f"- {rec}")
                st.write("")
            if st.button("💾 Log predictions", key="health_r_log"):
                for risk in risks:
                    ui.safe_log(
                        f"{risk['disease'].lower()} risk",
                        db.log_health_prediction,
                        user_id, f"risk_{risk['disease'].lower()}",
                        risk["probability_pct"], risk["risk_level"], confidence=1.0,
                        input_data={"age": age, "gender": gender, "height_cm": risk_height, "weight_kg": risk_weight, "activity_level": risk_activity, "daily_calories": risk_calories, "exercise_frequency": risk_freq},
                        output_data=risk,
                    )
                flash("Predictions logged to your history.")

        # --------------------------- Model Status --------------------------- #
        with ai_tab[4]:
            ui.render_model_status("health")
