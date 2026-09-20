"""
pages_app/dashboard.py
Milestone 4: Interactive Digital Twin Dashboard.

Provides a professional high-level overview across all domains:
    - KPI cards (only those supported by the available data)
    - Overview tab
    - Financial tab (income vs expenses, savings trend, projection, goals)
    - Study & Productivity tab (weekly hours, performance trend)
    - Habit & Lifestyle tab (completion rates)
    - Fitness tab (activity trend)
    - Simulation & Recommendations tab
    - Conversational AI tab

All charts use the user's real data from the existing database services. No
fake/static values are fabricated to make a chart look populated.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db
from ai.context_builder import run_simulation_snapshot
from ai_models.common import streamlit_ui as ui
from simulation.comparator import get_comparison_table
from utils import render_flash

DEFAULT_HABITS = ["Exercise Frequency", "Sleep Schedule", "Reading Habit", "Meal Prep"]


def render():
    render_flash()
    user_id = st.session_state.user_id
    user = db.get_user(user_id) or {}

    st.markdown("### 🏠 Digital Twin Dashboard")
    st.caption(
        "A high-level, real-time view of your finances, studies, habits, fitness, "
        "goals, forecasts, simulations and recommendations."
    )

    # ----------------------------- KPI cards ----------------------------- #
    _render_kpis(user_id, user)

    tabs = st.tabs([
        "Overview",
        "Financial",
        "Study & Productivity",
        "Habit & Lifestyle",
        "Fitness",
        "Simulation & Recommendations",
        "Conversational AI",
    ])

    with tabs[0]:
        _render_overview(user_id)
    with tabs[1]:
        _render_financial(user_id)
    with tabs[2]:
        _render_study(user_id)
    with tabs[3]:
        _render_habits(user_id)
    with tabs[4]:
        _render_fitness(user_id)
    with tabs[5]:
        _render_simulations(user_id)
    with tabs[6]:
        from pages_app import ai_chat
        ai_chat.render()


# =========================================================================== #
# KPI cards
# =========================================================================== #
def _render_kpis(user_id: int, user: dict) -> None:
    fin_summary = db.get_user_financial_summary(user_id)
    goals = db.get_goals(user_id)
    study = db.get_study_activities(user_id)
    habits = db.get_habits(user_id)
    fitness = db.get_fitness_records(user_id)
    sims = db.get_simulations(user_id, limit=1)

    kpis = []

    if not fin_summary.get("total_savings", 0) == 0 or fin_summary.get("monthly_income", 0) > 0:
        kpis.append(("Current Savings", f"₹{fin_summary.get('total_savings', 0):,.0f}"))

    if fin_summary.get("monthly_income", 0) > 0:
        kpis.append(("Monthly Savings", f"₹{fin_summary.get('monthly_savings', 0):,.0f}"))

    if not goals.empty:
        pct = (goals["current_progress"].astype(float) / goals["target_amount"].astype(float)).clip(0, 1)
        kpis.append(("Goal Progress", f"{pct.mean() * 100:.0f}%"))

    if not study.empty:
        avg_score = float(study["performance_score"].astype(float).mean())
        kpis.append(("Study Performance", f"{avg_score:.0f}/100"))

    if not habits.empty:
        avg_rate = float(habits["completion_rate"].astype(float).mean())
        kpis.append(("Habit Completion", f"{avg_rate:.0f}%"))

    if not fitness.empty:
        avg_min = float(fitness["exercise_minutes"].astype(float).mean()) if "exercise_minutes" in fitness.columns else 0
        kpis.append(("Fitness Activity", f"{avg_min:.0f} min/day"))

    if kpis:
        cols = st.columns(len(kpis))
        for col, (label, value) in zip(cols, kpis):
            col.metric(label, value)


# =========================================================================== #
# Overview tab
# =========================================================================== #
def _render_overview(user_id: int) -> None:
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("##### 💰 Savings Trend")
            history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)
            if history.empty:
                st.caption("No financial data yet.")
            else:
                fig = ui.figure(250)
                fig.add_trace(go.Scatter(
                    x=history["date"], y=history["cumulative_savings"],
                    mode="lines", name="Cumulative savings",
                    line=dict(color=ui.ACCENT, width=3),
                ))
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Projected (12 mo)", f"₹{projected_1yr:,.0f}")

    with col2:
        with st.container(border=True):
            st.markdown("##### 📚 Weekly Study Hours")
            weekly = db.get_weekly_study_hours(user_id)
            if weekly.empty or weekly["hours"].sum() == 0:
                st.caption("No study data yet.")
            else:
                fig = ui.figure(250)
                fig.add_trace(go.Bar(
                    x=weekly["day"], y=weekly["hours"],
                    marker_color=ui.ACCENT, name="Hours",
                ))
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Peak Focus", db.get_peak_focus_time(user_id))

    goals = db.get_goals(user_id)
    with st.container(border=True):
        st.markdown("##### 🎯 Goals & Progress")
        if goals.empty:
            st.caption("No goals set yet — add some in Personal Data & Profile.")
        else:
            for _, g in goals.iterrows():
                pct = min(float(g["current_progress"]) / float(g["target_amount"]) * 100, 100) if g["target_amount"] else 0
                st.progress(min(pct / 100, 1.0), text=f"{g['goal_name']} — {pct:.0f}%  (₹{g['current_progress']:,.0f} / ₹{g['target_amount']:,.0f})")


# =========================================================================== #
# Financial tab
# =========================================================================== #
def _render_financial(user_id: int) -> None:
    records = db.get_financial_records(user_id)
    if records.empty:
        st.info("No financial data yet. Add financial records to see analytics.")
        return

    records = records.copy()
    records["date"] = pd.to_datetime(records["date"], errors="coerce")

    # Income vs expenses
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### 💵 Income vs Expenses")
            grouped = records.groupby([records["date"].dt.to_period("M"), "transaction_type"])["amount"].sum().unstack(fill_value=0)
            months = [str(p) for p in grouped.index]
            fig = go.Figure()
            for ttype, color in [("Income", ui.ACCENT), ("Expense", "#fb7185"), ("Savings", "#34d399")]:
                if ttype in grouped.columns:
                    fig.add_trace(go.Bar(x=months, y=grouped[ttype], name=ttype, marker_color=color))
            _style(fig, y_title="Amount (₹)")
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("##### 📈 Savings Projection")
            history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)
            horizon = st.slider("Forecast horizon (months)", 1, 36, 12, key="dash_fin_horizon")
            if not history.empty:
                last_date = pd.to_datetime(history["date"]).iloc[-1]
                last_val = history["cumulative_savings"].iloc[-1]
                future_dates = [last_date + pd.Timedelta(days=30 * m) for m in range(1, horizon + 1)]
                future_vals = [last_val + monthly_rate * m for m in range(1, horizon + 1)]
                fig = ui.figure(250)
                fig.add_trace(go.Scatter(x=history["date"], y=history["cumulative_savings"], mode="lines", name="Actual", line=dict(color=ui.ACCENT, width=3)))
                fig.add_trace(go.Scatter(x=[last_date] + future_dates, y=[last_val] + future_vals, mode="lines+markers", name="Projected (forecast)", line=dict(color="#d946ef", width=2, dash="dash")))
                _style(fig, y_title="Savings (₹)")
                st.plotly_chart(fig, use_container_width=True)
                st.metric(f"Projected ({horizon} mo)", f"₹{future_vals[-1]:,.0f}")

    # Spending by category
    with st.container(border=True):
        st.markdown("##### 🍽️ Spending by Category")
        expenses = records[records["transaction_type"] == "Expense"]
        if expenses.empty:
            st.caption("No expense records yet.")
        else:
            cat = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
            fig = ui.figure(260)
            fig.add_trace(go.Bar(x=cat.values, y=cat.index, orientation="h", marker_color=ui.ACCENT))
            _style(fig, x_title="Amount (₹)", y_title="")
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================== #
# Study tab
# =========================================================================== #
def _render_study(user_id: int) -> None:
    study = db.get_study_activities(user_id)
    if study.empty:
        st.info("No study data yet. Log study activities to see analytics.")
        return

    study = study.copy()
    study["date"] = pd.to_datetime(study["date"], errors="coerce")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### 📅 Study Hours Over Time")
            daily = study.groupby(study["date"].dt.date)["hours_logged"].sum().reset_index()
            fig = ui.figure(250)
            fig.add_trace(go.Bar(x=daily.iloc[:, 0], y=daily["hours_logged"], marker_color=ui.ACCENT, name="Hours"))
            _style(fig, y_title="Hours")
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("##### 📈 Performance Trend")
            scored = study.dropna(subset=["performance_score"])
            if scored.empty:
                st.caption("No performance scores logged yet.")
            else:
                per_day = scored.groupby(scored["date"].dt.date)["performance_score"].mean().reset_index()
                fig = ui.figure(250)
                fig.add_trace(go.Scatter(x=per_day.iloc[:, 0], y=per_day["performance_score"], mode="lines+markers", name="Score", line=dict(color=ui.ACCENT, width=3)))
                _style(fig, y_title="Score (0-100)", yrange=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

    # Weekly hours + performance prediction
    with st.container(border=True):
        st.markdown("##### 🗓️ Weekly Study Pattern")
        weekly = db.get_weekly_study_hours(user_id)
        if not weekly.empty and weekly["hours"].sum() > 0:
            fig = ui.figure(260)
            fig.add_trace(go.Bar(x=weekly["day"], y=weekly["hours"], marker_color=ui.ACCENT, name="Hours"))
            _style(fig, y_title="Hours")
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================== #
# Habits tab
# =========================================================================== #
def _render_habits(user_id: int) -> None:
    habits = db.get_habits(user_id)
    if habits.empty:
        st.info("No habit data yet. Log habits to see consistency analytics.")
        return

    habit_names = db.get_habit_names(user_id) or DEFAULT_HABITS
    with st.container(border=True):
        st.markdown("##### ✅ Habit Completion Rates")
        rows = []
        for name in habit_names:
            pred = db.get_habit_prediction_by_name(user_id, name)
            rows.append({"habit": name, "rate": pred["rate"], "trend": pred["trend_pct"]})
        if rows:
            df = pd.DataFrame(rows).sort_values("rate", ascending=False)
            fig = ui.figure(280)
            colors = ["#34d399" if r >= 75 else ("#fbbf24" if r >= 45 else "#fb7185") for r in df["rate"]]
            fig.add_trace(go.Bar(x=df["habit"], y=df["rate"], marker_color=colors, name="Completion %"))
            _style(fig, y_title="Completion (%)", yrange=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

            st.caption("Positive/negative trend (%) per habit:")
            trend_text = "  •  ".join(
                f"{r['habit']}: {r['trend']:+.1f}%" for r in rows
            )
            st.markdown(trend_text)


# =========================================================================== #
# Fitness tab
# =========================================================================== #
def _render_fitness(user_id: int) -> None:
    fitness = db.get_fitness_records(user_id)
    if fitness.empty:
        st.info("No fitness data yet. Log fitness records (Habit Tracker) to see activity analytics.")
        return

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### 🏃 Activity Over Time")
            if "date" not in fitness.columns:
                fitness = fitness.rename(columns={"record_date": "date"})
            fitness["date"] = pd.to_datetime(fitness["date"], errors="coerce")
            fig = go.Figure()
            if "steps" in fitness.columns:
                fig.add_trace(go.Scatter(x=fitness["date"], y=fitness["steps"], mode="lines+markers", name="Steps", line=dict(color=ui.ACCENT, width=3)))
            if "exercise_minutes" in fitness.columns:
                fig.add_trace(go.Scatter(x=fitness["date"], y=fitness["exercise_minutes"], mode="lines+markers", name="Exercise (min)", yaxis="y2", line=dict(color="#d946ef", width=2, dash="dash")))
            fig.update_layout(yaxis2=dict(overlaying="y", side="right", color="#cbd5e1", gridcolor="rgba(255,255,255,0.06)"))
            _style(fig, y_title="Steps")
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("##### 💤 Sleep & Duration Trend")
            fig = go.Figure()
            if "sleep_hours" in fitness.columns:
                fig.add_trace(go.Scatter(x=fitness["date"], y=fitness["sleep_hours"], mode="lines+markers", name="Sleep (h)", line=dict(color="#34d399", width=3)))
            if "exercise_minutes" in fitness.columns:
                fig.add_trace(go.Scatter(x=fitness["date"], y=fitness["exercise_minutes"], mode="lines+markers", name="Exercise (min)", line=dict(color="#fbbf24", width=2, dash="dash")))
            _style(fig, y_title="Value")
            st.plotly_chart(fig, use_container_width=True)


# =========================================================================== #
# Simulation & Recommendations tab
# =========================================================================== #
def _render_simulations(user_id: int) -> None:
    recommendations = db.get_recommendations(user_id, limit=5)
    if not recommendations.empty:
        with st.container(border=True):
            st.markdown("##### 🤖 Personalized Recommendations")
            for _, r in recommendations.iterrows():
                col = st.columns([1, 4])[1]
                cat = r.get("category") or "general"
                priority = r.get("priority") or "medium"
                text = r.get("recommendation_text") or r.get("reason") or "—"
                st.markdown(f"**[{cat} · {priority}]** {text}")
                if r.get("reason"):
                    st.caption(f"Reason: {r['reason']}")
                st.write("")

    with st.container(border=True):
        st.markdown("##### 🧬 Run a quick Simulation")
        domain_label = st.selectbox("Domain", ["Financial", "Study & Productivity", "Habit & Fitness"], key="dash_sim_domain")
        horizon = st.slider("Horizon (months)", 3, 36, 12, step=3, key="dash_sim_horizon")
        domain_key = {"Financial": "finance", "Study & Productivity": "study", "Habit & Fitness": "habits"}[domain_label]

        if st.button("🚀 Run Simulation", type="primary", key="dash_run_sim"):
            import time
            start = time.time()
            try:
                result = run_simulation_snapshot(user_id, domain_key, horizon)
                _display_simulation_result(result, domain_key)
                elapsed = time.time() - start
                st.caption(f"⏱️ Simulation completed in {elapsed:.2f}s")
            except Exception as e:
                st.error(f"Could not run simulation: {e}")

    saved = db.get_simulations(user_id, limit=5)
    if not saved.empty:
        with st.expander("📂 Saved Simulations"):
            for _, s in saved.iterrows():
                scenarios = db.get_simulation_scenarios(int(s["simulation_id"]))
                best_line = "n/a"
                if not scenarios.empty:
                    top = scenarios.sort_values("score", ascending=False).iloc[0]
                    best_line = f"{top['scenario_name']} ({top['score']:.1f}/100)"
                st.markdown(f"**{s['title']}** — {s['simulation_type']} · {s.get('horizon_months')} mo")
                st.caption(f"Best scenario: {best_line}")


def _display_simulation_result(result: dict, domain: str) -> None:
    scenarios = result["scenarios"]
    recommendation = result["recommendation"]

    with st.container(border=True):
        st.markdown("##### 📈 Scenario Comparison")
        fig = go.Figure()
        palette = ["#22d3ee", "#d946ef", "#fbbf24", "#34d399", "#fb7185", "#818cf8"]
        y_key = {
            "finance": ("balance", "Projected Balance (₹)"),
            "study": ("projected_score", "Projected Score"),
            "habits": ("projected_fitness_score", "Projected Fitness Score"),
        }.get(domain, ("balance", "Value"))
        for idx, s in enumerate(scenarios):
            color = palette[idx % len(palette)]
            width = 4 if s.is_baseline else 2.5
            x = [t["month"] for t in s.time_series]
            y = [t[y_key[0]] for t in s.time_series]
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=s.name,
                                     line=dict(color=color, width=width, dash="solid" if s.is_baseline else None)))
        _style(fig, y_title=y_key[1], x_title="Month")
        st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("##### 📋 Scenario Results")
        table = get_comparison_table(scenarios, domain)
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    if recommendation:
        with st.container(border=True):
            st.markdown("##### 🤖 Recommendation")
            st.markdown(f"**Recommended: {recommendation['recommended_scenario']}**")
            st.info(f"**Why:** {recommendation['reason']}")
            if recommendation.get("benefits"):
                st.markdown("**Benefits:**")
                for b in recommendation["benefits"]:
                    st.markdown(f"  ✅ {b}")
            if recommendation.get("risks"):
                st.markdown("**Risks / Trade-offs:**")
                for r in recommendation["risks"]:
                    st.markdown(f"  ⚠️ {r}")


# =========================================================================== #
# Style helper (dark theme consistent with the rest of the app)
# =========================================================================== #
def _style(fig: go.Figure, x_title: str = "", y_title: str = "",
           xrange=None, yrange=None) -> None:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", family="Inter, sans-serif"),
        legend=dict(orientation="h", y=1.12, font=dict(color="#cbd5e1")),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title=x_title, color="#cbd5e1", tickfont=dict(color="#cbd5e1"),
                   title_font=dict(color="#cbd5e1"), gridcolor="rgba(255,255,255,0.06)",
                   range=xrange),
        yaxis=dict(title=y_title, color="#cbd5e1", tickfont=dict(color="#cbd5e1"),
                   title_font=dict(color="#cbd5e1"), gridcolor="rgba(255,255,255,0.06)",
                   range=yrange),
    )
