"""
pages_app/habits.py
Habit Tracker tab: CRUD on Habits + Milestone 2 habit predictions
(progress bars / trend insights for key habit categories).
"""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_bridge  # noqa: F401  (links the Milestone 2 AI Core Layer)

import database as db
from ai_models.common import streamlit_ui as ui
from ai_models.fitness import predict as fit_ai
from utils import flash, render_flash

DEFAULT_HABIT_CATEGORIES = ["Exercise Frequency", "Sleep Schedule", "Reading Habit", "Meal Prep"]


def render():
    render_flash()

    user_id = st.session_state.user_id

    st.markdown("### ✅ Habit Tracker")

    # ------------------------- Predictions ------------------------- #
    # Fix 7: fetch every habit name actually logged for this user_id from
    # PostgreSQL (including custom habits), instead of a hardcoded list.
    logged_names = db.get_habit_names(user_id)
    display_categories = logged_names if logged_names else DEFAULT_HABIT_CATEGORIES

    with st.container(border=True):
        st.markdown("#### 🔮 Habit Predictions")
        cols = st.columns(2)
        for i, category in enumerate(display_categories):
            pred = db.get_habit_prediction_by_name(user_id, category)
            with cols[i % 2]:
                st.markdown(f"**{category}**")
                st.progress(min(pred["rate"] / 100, 1.0), text=f"{pred['rate']:.0f}% consistency")
                trend_symbol = "▲" if pred["trend_pct"] > 0 else ("▼" if pred["trend_pct"] < 0 else "→")
                st.caption(f"{trend_symbol} {pred['trend_pct']:+.1f}% vs earlier · {pred['insight']}")
                st.write("")

    # ------------------------------ CRUD ------------------------------ #
    with st.container(border=True):
        st.markdown("#### ➕ Log a Habit")
        with st.form("habit_add_form"):
            habit_name = st.selectbox("Habit", DEFAULT_HABIT_CATEGORIES + ["Custom"])
            if habit_name == "Custom":
                habit_name = st.text_input("Custom habit name")
            c1, c2 = st.columns(2)
            status = c1.selectbox("Status", ["Done", "Partial", "Missed"])
            completion = c2.slider("Completion rate (%)", 0, 100, 70)
            hdate = st.date_input("Date", value=date.today())
            if st.form_submit_button("Save Entry", use_container_width=True):
                if habit_name:
                    db.add_habit(user_id, habit_name, status, completion, hdate)
                    flash("Habit entry saved.")
                    st.rerun()
                else:
                    flash("Please name the habit.", "error")

    with st.container(border=True):
        st.markdown("#### 📋 Habit Log")
        habits_df = db.get_habits(user_id)
        if habits_df.empty:
            st.caption("No habits logged yet.")
        else:
            display_df = habits_df[["habit_id", "habit_name", "status", "completion_rate", "date"]]
            edited = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                disabled=["habit_id"],
                column_config={
                    "habit_id": "ID",
                    "habit_name": "Habit",
                    "status": st.column_config.SelectboxColumn("Status", options=["Done", "Partial", "Missed"]),
                    "completion_rate": st.column_config.NumberColumn("Completion %", format="%.0f"),
                    "date": "Date",
                },
                num_rows="fixed",
                key="habit_editor",
            )
            col_a, col_b = st.columns(2)
            if col_a.button("💾 Save Changes", key="habit_save_changes"):
                for _, row in edited.iterrows():
                    db.update_habit(
                        int(row["habit_id"]),
                        habit_name=row["habit_name"],
                        status=row["status"],
                        completion_rate=float(row["completion_rate"]),
                        date=row["date"],
                    )
                flash("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete an entry"):
                del_id = st.selectbox("Habit ID to delete", display_df["habit_id"].tolist())
                if st.button("Confirm Delete", key="habit_delete_confirm"):
                    db.delete_habit(int(del_id))
                    flash("Entry deleted.", "info")
                    st.rerun()

    # ------------------------- AI Core (Milestone 2) ------------------------- #
    with st.container(border=True):
        st.markdown("#### 🏃 AI Fitness Assistant")
        ai_tab = st.tabs(
            ["Fitness Score", "Workout Recommendation", "Activity Trend", "Goal Achievement", "Model Status"]
        )
        fitness_records = db.get_fitness_records(user_id)
        health_records = db.get_health_records(user_id)
        last_health = db.get_latest_health(user_id)

        default_bmi = 24.0
        if last_health.get("height_cm") and last_health.get("weight_kg"):
            default_bmi = last_health["weight_kg"] / (last_health["height_cm"] / 100) ** 2

        # ------------------------- Fitness Score ------------------------- #
        with ai_tab[0]:
            st.markdown("**Log today's fitness data and predict your score**")
            c1, c2, c3, c4 = st.columns(4)
            steps = c1.number_input("Steps", 0, 50000, 7000, 100, key="fit_steps")
            exercise_min = c2.number_input("Exercise (minutes)", 0, 600, 30, 5, key="fit_exercise")
            sleep_hours = c3.number_input("Sleep (hours)", 0.0, 24.0, 7.0, 0.1, key="fit_sleep")
            water = c4.number_input("Water (litres)", 0.0, 15.0, 2.2, 0.1, key="fit_water")
            calories_burned = st.number_input("Calories burned (kcal)", 0.0, 3000.0, 250.0, 10.0, key="fit_calories")
            freq = st.slider("Exercise frequency (days/week)", 0, 7, 3, key="fit_freq")

            result = fit_ai.predict_fitness_score(int(freq), int(steps), sleep_hours, calories_burned, default_bmi)
            st.metric("Fitness score", f"{result['score']:.0f}/100", result["level"].capitalize())
            st.progress(min(result["score"] / 100, 1.0))

            if st.button("💾 Save data & log prediction", key="fit_save"):
                ui.safe_log("fitness record", db.add_fitness_record, user_id, date.today(), int(steps), exercise_min, sleep_hours, water, calories_burned, int(freq))
                ui.safe_log(
                    "fitness score prediction",
                    db.log_fitness_prediction,
                    user_id, "fitness_score",
                    result["score"], result["level"].capitalize(), confidence=1.0,
                    input_data={"steps": steps, "exercise_minutes": exercise_min, "sleep_hours": sleep_hours, "calories_burned": calories_burned, "bmi": round(default_bmi, 1)},
                    output_data=result,
                )
                flash("Saved to your profile & history.")

        # --------------------- Workout Recommendation --------------------- #
        with ai_tab[1]:
            st.markdown("**Get a personalised workout plan**")
            goal = st.selectbox("Goal", ["maintain", "lose", "gain"], key="fit_goal")
            score_input = st.slider("Current fitness score (0-100)", 0, 100, 50, key="fit_score_slider")
            if st.button("Recommend workout", key="fit_recommend"):
                plan = fit_ai.recommend_workout(score_input, default_bmi, goal)
                ui.render_metrics(
                    {"Level": plan["level"], "Duration": f"{plan['duration_minutes']} min", "Calorie target": f"~{plan['calories_target']} kcal"},
                    columns=3,
                )
                st.markdown("**Recommended exercises**")
                for ex in plan["exercises"]:
                    st.markdown(f"- {ex}")
                if plan["notes"]:
                    st.caption(" • ".join(plan["notes"]))
                ui.safe_log(
                    "workout recommendation",
                    db.log_fitness_prediction,
                    user_id, "workout_recommendation",
                    plan["calories_target"], plan["level"], confidence=1.0,
                    input_data={"score": score_input, "bmi": round(default_bmi, 1), "goal": goal}, output_data=plan,
                )

        # ------------------------ Activity Trend ------------------------ #
        with ai_tab[2]:
            st.markdown("**Weekly activity forecast & inactivity detection**")
            if not fitness_records.empty and "date" in fitness_records.columns:
                activity_df = fitness_records[["date", "steps", "exercise_minutes"]]
            elif not fitness_records.empty and "record_date" in fitness_records.columns:
                activity_df = fitness_records[["record_date", "steps", "exercise_minutes"]].rename(columns={"record_date": "date"})
            else:
                activity_df = pd.DataFrame(columns=["date", "steps", "exercise_minutes"])
            weeks_ahead = st.slider("Forecast horizon (weeks)", 4, 16, 8, key="fit_trend_weeks")
            trend = fit_ai.predict_weekly_activity(activity_df, weeks_ahead=weeks_ahead)
            if trend["forecast"].empty:
                st.caption("Log fitness data above to forecast your activity trend.")
            else:
                if trend["inactive"]:
                    st.warning(f"Inactive detected — average {trend['avg_daily_steps']:.0f} steps/day. {trend['message']}")
                else:
                    st.success(trend["message"])
                bar = ui.figure(280)
                bar.add_trace(go.Bar(x=trend["forecast"]["week"], y=trend["forecast"]["predicted_steps"], marker_color=ui.ACCENT))
                st.plotly_chart(bar, use_container_width=True)
                st.dataframe(trend["forecast"], hide_index=True, use_container_width=True)
                ui.safe_log(
                    "activity trend",
                    db.log_fitness_prediction,
                    user_id, "activity_trend",
                    float(trend["forecast"]["predicted_steps"].mean()), "Weekly forecast",
                    input_data={"avg_daily_steps": trend["avg_daily_steps"], "inactive": trend["inactive"]},
                    output_data=trend["forecast"].to_dict("records"),
                )

        # ---------------------- Goal Achievement ---------------------- #
        with ai_tab[3]:
            st.markdown("**Chance of reaching your fitness goal**")
            c1, c2, c3 = st.columns(3)
            current_goal = c1.number_input("Current score", 0, 100, 50, key="fit_goal_current")
            target_goal = c2.number_input("Goal score", 0, 100, 80, key="fit_goal_target")
            days_left = c3.number_input("Days to goal", 7, 365, 90, key="fit_goal_days")
            outcome = fit_ai.predict_goal_achievement(current_goal, target_goal, int(days_left), int(freq), int(steps), sleep_hours)
            st.metric("Probability", f"{outcome['probability_pct']:.0f}%", outcome["level"])
            st.progress(min(outcome["probability_pct"] / 100, 1.0))
            st.info(outcome["recommendation"])
            if st.button("💾 Log prediction", key="fit_goal_log"):
                ui.safe_log(
                    "goal achievement",
                    db.log_fitness_prediction,
                    user_id, "goal_achievement",
                    outcome["probability_pct"], outcome["level"], confidence=1.0,
                    input_data={"current_score": current_goal, "goal_score": target_goal, "days_to_goal": days_left},
                    output_data=outcome,
                )
                flash("Prediction logged to your history.")

        # --------------------------- Model Status --------------------------- #
        with ai_tab[4]:
            ui.render_model_status("fitness")
