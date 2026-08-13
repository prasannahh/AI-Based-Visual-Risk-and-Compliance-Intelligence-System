"""
pages_app/dashboard.py
Overview dashboard: avatar summary, goals snapshot, savings mini-chart,
study mini-chart, and habit predictions snapshot.
"""

from datetime import date

import plotly.graph_objects as go
import streamlit as st

import database as db
from ui_components import render_avatar_block

DEFAULT_HABIT_CATEGORIES = ["Exercise Frequency", "Sleep Schedule", "Reading Habit", "Meal Prep"]


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
        st.markdown(
            f"<div style='text-align:center;color:#0e7490;font-weight:600;padding-top:0.4rem;'>"
            f"👋 Good to see you, {user['name'].split()[0]}!</div>",
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)

    # --------------------------- Savings mini-chart --------------------------- #
    with col1:
        with st.container(border=True):
            st.markdown("##### 💰 Savings Trend")
            history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)
            if history.empty:
                st.caption("No financial data yet.")
            else:
                fig = go.Figure(
                    go.Scatter(x=history["date"], y=history["cumulative_savings"], mode="lines", line=dict(color="#0891b2", width=3))
                )
                fig.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#000000"),
                    xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                    yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                    margin=dict(l=0, r=0, t=0, b=0), height=160, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Projected (1yr)", f"₹{projected_1yr:,.0f}")

    # --------------------------- Study mini-chart --------------------------- #
    with col2:
        with st.container(border=True):
            st.markdown("##### 📚 Weekly Study Hours")
            weekly = db.get_weekly_study_hours(user_id)
            if weekly.empty or weekly["hours"].sum() == 0:
                st.caption("No study data yet.")
            else:
                fig = go.Figure(go.Bar(x=weekly["day"], y=weekly["hours"], marker_color="#0891b2"))
                fig.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#000000"),
                    xaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                    yaxis=dict(color="#000000", tickfont=dict(color="#000000")),
                    margin=dict(l=0, r=0, t=0, b=0), height=160, showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Peak Focus", db.get_peak_focus_time(user_id))

    # --------------------------- Habit ring snapshot --------------------------- #
    with col3:
        with st.container(border=True):
            st.markdown("##### ✅ Habit Snapshot")
            # Fix 7: pull every habit logged for this user_id (custom habits
            # included) rather than a hardcoded 4-item list.
            logged_names = db.get_habit_names(user_id)
            display_habits = logged_names if logged_names else DEFAULT_HABIT_CATEGORIES
            rates = [db.get_habit_prediction_by_name(user_id, c)["rate"] for c in display_habits]
            avg_rate = sum(rates) / len(rates) if rates else 0
            st.progress(min(avg_rate / 100, 1.0), text=f"Average consistency: {avg_rate:.0f}%")
            for c, r in list(zip(display_habits, rates))[:5]:
                st.caption(f"{c}: {r:.0f}%")
            if len(display_habits) > 5:
                st.caption(f"+{len(display_habits) - 5} more habit(s) tracked")

    # --------------------------- Goals overview --------------------------- #
    with st.container(border=True):
        st.markdown("##### 🎯 Goals & Progress")
        if goals.empty:
            st.caption("No goals set yet — head to Personal Data & Profile to add one.")
        else:
            for _, g in goals.iterrows():
                pct = min(float(g["current_progress"]) / float(g["target_amount"]) * 100, 100) if g["target_amount"] else 0
                st.progress(min(pct / 100, 1.0), text=f"{g['goal_name']} — {pct:.0f}%")