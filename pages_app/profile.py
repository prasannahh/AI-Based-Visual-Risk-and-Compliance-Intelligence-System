"""
pages_app/profile.py
Milestone 1: Data Collection & User Profiling.
Avatar & summary, Goals card, Add New Data form, Today's Schedule editor,
Behavioral Patterns widget.
"""

from datetime import date, time

import pandas as pd
import streamlit as st

import database as db
from ui_components import render_avatar_block
from utils import trend_html


def render():
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
                        if c1.button("Save", key=f"save_goal_{g['goal_id']}", use_container_width=True):
                            db.update_goal_progress(g["goal_id"], new_val)
                            st.success("Goal updated.")
                            st.rerun()
                        if c2.button("Delete", key=f"del_goal_{g['goal_id']}", use_container_width=True):
                            db.delete_goal(g["goal_id"])
                            st.rerun()

            with st.expander("➕ Add a new goal"):
                with st.form("add_goal_form"):
                    gname = st.text_input("Goal name (e.g., Emergency Fund)")
                    gtarget = st.number_input("Target amount", min_value=0.0, value=1000.0)
                    gcurrent = st.number_input("Current progress", min_value=0.0, value=0.0)
                    gdate = st.date_input("Target date", value=date.today())
                    if st.form_submit_button("Add Goal", use_container_width=True):
                        if gname:
                            db.add_goal(user_id, gname, gtarget, gcurrent, gdate)
                            st.success("Goal added.")
                            st.rerun()
                        else:
                            st.error("Please name your goal.")

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
                if st.form_submit_button("Save Entry", use_container_width=True):
                    db.add_financial_record(user_id, category, amount, ttype, fdate)
                    st.success("Financial record saved.")
                    st.rerun()

        elif entry_type == "Study":
            with st.form("study_form"):
                subject = st.text_input("Subject")
                c1, c2 = st.columns(2)
                hours = c1.number_input("Hours logged", min_value=0.0, value=1.0, step=0.5)
                score = c2.number_input("Performance score (0-100)", min_value=0.0, max_value=100.0, value=75.0)
                sdate = st.date_input("Date", value=date.today(), key="study_date")
                if st.form_submit_button("Save Entry", use_container_width=True):
                    if subject:
                        db.add_study_activity(user_id, subject, hours, score, sdate)
                        st.success("Study activity saved.")
                        st.rerun()
                    else:
                        st.error("Please enter a subject.")

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
                if st.form_submit_button("Save Entry", use_container_width=True):
                    if habit_name:
                        db.add_habit(user_id, habit_name, status, completion, hdate)
                        st.success("Habit entry saved.")
                        st.rerun()
                    else:
                        st.error("Please name the habit.")

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
            use_container_width=True,
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
            st.success("Schedule saved.")
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
