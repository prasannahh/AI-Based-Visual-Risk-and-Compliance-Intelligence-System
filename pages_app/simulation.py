"""
pages_app/simulation.py
Milestone 3: Digital Twin Simulation Engine page.

Allows users to run "what-if" decision simulations across financial,
study, and habit/fitness domains. Compares multiple future scenarios,
scores them, and provides personalized recommendations.
"""

import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db
from ai_models.common import streamlit_ui as ui
from simulation.comparator import get_comparison_table
from simulation.engine import (
    SimulationRequest,
    run_simulation,
)
from simulation.recommendation import generate_recommendation
from utils import flash, render_flash


def render():
    render_flash()

    user_id = st.session_state.user_id

    st.markdown("### 🧬 Digital Twin Simulation")
    st.caption("Simulate decisions and compare future outcomes — powered by your real data.")

    # ------------------------- Domain Selection ------------------------- #
    with st.container(border=True):
        st.markdown("#### 🎯 Simulate a Decision")
        c1, c2 = st.columns(2)
        domain = c1.selectbox(
            "Domain",
            ["Financial", "Study & Productivity", "Habit & Fitness"],
            key="sim_domain",
        )
        horizon_months = c2.slider(
            "Forecast horizon (months)",
            min_value=3,
            max_value=60,
            value=12,
            step=3,
            key="sim_horizon",
        )

    domain_key = {"Financial": "finance", "Study & Productivity": "study", "Habit & Fitness": "habits"}[domain]

    # ------------------------- Financial Simulation ------------------------- #
    if domain_key == "finance":
        _render_financial_simulation(user_id, horizon_months)

    # ------------------------- Study Simulation ------------------------- #
    elif domain_key == "study":
        _render_study_simulation(user_id, horizon_months)

    # ------------------------- Habit/Fitness Simulation ------------------------- #
    elif domain_key == "habits":
        _render_habit_simulation(user_id, horizon_months)


def _render_financial_simulation(user_id: int, horizon_months: int):
    fin_summary = db.get_user_financial_summary(user_id)
    goals = db.get_user_goals(user_id)

    with st.container(border=True):
        st.markdown("#### 📊 Current Financial State")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Monthly Income", f"₹{fin_summary['monthly_income']:,.0f}")
        c2.metric("Monthly Expenses", f"₹{fin_summary['monthly_expenses']:,.0f}")
        c3.metric("Monthly Savings", f"₹{fin_summary['monthly_savings']:,.0f}")
        c4.metric("Total Savings", f"₹{fin_summary['total_savings']:,.0f}")

        if goals:
            st.markdown("**Active Goals**")
            for g in goals:
                pct = (g["current_progress"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
                st.caption(f"• {g['goal_name']}: ₹{g['current_progress']:,.0f} / ₹{g['target_amount']:,.0f} ({pct:.0f}%)")

    with st.container(border=True):
        st.markdown("#### ⚙️ Customize Scenarios")
        st.caption("The system will auto-generate scenarios based on your data. You can also define custom ones.")

        use_custom = st.checkbox("Define custom scenarios", key="fin_use_custom")
        custom_scenarios = []
        if use_custom:
            num_custom = st.number_input("Number of custom scenarios", 1, 5, 2, key="fin_num_custom")
            for i in range(int(num_custom)):
                with st.expander(f"Custom Scenario {i + 1}"):
                    cname = st.text_input(f"Name", value=f"Scenario {i + 1}", key=f"fin_cname_{i}")
                    csaving = st.number_input(
                        f"Monthly savings (₹)",
                        min_value=0.0,
                        value=float(fin_summary["monthly_savings"]),
                        step=500.0,
                        key=f"fin_csaving_{i}",
                    )
                    cexpense = st.number_input(
                        f"Monthly expenses (₹)",
                        min_value=0.0,
                        value=float(fin_summary["monthly_expenses"]),
                        step=500.0,
                        key=f"fin_cexpense_{i}",
                    )
                    custom_scenarios.append({
                        "name": cname,
                        "description": f"Save ₹{csaving:,.0f}, spend ₹{cexpense:,.0f}/month",
                        "monthly_saving": csaving,
                        "monthly_expenses": cexpense,
                    })

    if st.button("🚀 Run Financial Simulation", type="primary", key="run_fin_sim", width="stretch"):
        _run_and_display_simulation(
            user_id=user_id,
            domain="finance",
            horizon_months=horizon_months,
            params={
                "financial": fin_summary,
                "goals": goals,
                "scenarios": custom_scenarios if custom_scenarios else None,
            },
        )


def _render_study_simulation(user_id: int, horizon_months: int):
    study_summary = db.get_user_study_summary(user_id)

    with st.container(border=True):
        st.markdown("#### 📊 Current Study State")
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Hours/Day", f"{study_summary['avg_hours_per_day']:.1f}h")
        c2.metric("Avg Performance", f"{study_summary['avg_performance_score']:.0f}/100")
        c3.metric("Subjects", ", ".join(study_summary["subjects"][:3]) if study_summary["subjects"] else "None")

        consistency = st.slider(
            "Current study consistency (0-1)",
            0.0, 1.0, 0.6,
            key="sim_study_consistency",
        )

    with st.container(border=True):
        st.markdown("#### ⚙️ Customize Scenarios")
        use_custom = st.checkbox("Define custom study scenarios", key="study_use_custom")
        custom_scenarios = []
        if use_custom:
            num_custom = st.number_input("Number of custom scenarios", 1, 5, 2, key="study_num_custom")
            for i in range(int(num_custom)):
                with st.expander(f"Custom Scenario {i + 1}"):
                    cname = st.text_input("Name", value=f"Study Scenario {i + 1}", key=f"study_cname_{i}")
                    chours = st.number_input(
                        "Hours per day",
                        min_value=0.0, max_value=16.0,
                        value=study_summary["avg_hours_per_day"],
                        step=0.5,
                        key=f"study_chours_{i}",
                    )
                    custom_scenarios.append({
                        "name": cname,
                        "description": f"Study {chours:.1f} hours/day",
                        "hours_per_day": chours,
                    })

    if st.button("🚀 Run Study Simulation", type="primary", key="run_study_sim", width="stretch"):
        _run_and_display_simulation(
            user_id=user_id,
            domain="study",
            horizon_months=horizon_months,
            params={
                "study": study_summary,
                "consistency": consistency,
                "scenarios": custom_scenarios if custom_scenarios else None,
            },
        )


def _render_habit_simulation(user_id: int, horizon_months: int):
    habit_summary = db.get_user_habit_summary(user_id)

    with st.container(border=True):
        st.markdown("#### 📊 Current Habit & Fitness State")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Habit Completion", f"{habit_summary['avg_completion_rate']:.0f}%")
        c2.metric("Exercise Freq", f"{habit_summary['exercise_frequency']} days/week")
        c3.metric("Avg Steps", f"{habit_summary['avg_steps']:,.0f}")
        c4.metric("Avg Sleep", f"{habit_summary['avg_sleep_hours']:.1f}h")

    with st.container(border=True):
        st.markdown("#### ⚙️ Customize Scenarios")
        use_custom = st.checkbox("Define custom habit scenarios", key="habit_use_custom")
        custom_scenarios = []
        if use_custom:
            num_custom = st.number_input("Number of custom scenarios", 1, 5, 2, key="habit_num_custom")
            for i in range(int(num_custom)):
                with st.expander(f"Custom Scenario {i + 1}"):
                    cname = st.text_input("Name", value=f"Habit Scenario {i + 1}", key=f"habit_cname_{i}")
                    ccomp = st.slider(
                        "Completion rate (%)",
                        0, 100, int(habit_summary["avg_completion_rate"]),
                        key=f"habit_ccomp_{i}",
                    )
                    cfreq = st.slider(
                        "Exercise frequency (days/week)",
                        0, 7, habit_summary["exercise_frequency"],
                        key=f"habit_cfreq_{i}",
                    )
                    custom_scenarios.append({
                        "name": cname,
                        "description": f"Completion {ccomp}%, exercise {cfreq} days/week",
                        "completion_rate": float(ccomp),
                        "exercise_frequency": cfreq,
                    })

    if st.button("🚀 Run Habit Simulation", type="primary", key="run_habit_sim", width="stretch"):
        _run_and_display_simulation(
            user_id=user_id,
            domain="habits",
            horizon_months=horizon_months,
            params={
                "habits": habit_summary,
                "scenarios": custom_scenarios if custom_scenarios else None,
            },
        )


def _run_and_display_simulation(user_id: int, domain: str, horizon_months: int, params: dict):
    request = SimulationRequest(
        user_id=user_id,
        domain=domain,
        horizon_months=horizon_months,
        custom_params=params,
    )

    with st.spinner("Running simulation..."):
        start_time = time.time()
        result = run_simulation(request, params)
        elapsed = time.time() - start_time

    st.caption(f"Simulation completed in {elapsed:.2f}s")

    scenarios = result["scenarios"]
    recommendation = result["recommendation"]

    # ------------------------- Scenario Comparison Chart ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📈 Scenario Comparison")
        _render_comparison_chart(scenarios, domain, horizon_months)

    # ------------------------- Scenario Results Table ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📋 Scenario Results")
        table_data = get_comparison_table(scenarios, domain)
        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
        )

    # ------------------------- Time Series Charts ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📉 Future Projections")
        _render_time_series_charts(scenarios, domain, horizon_months)

    # ------------------------- Recommendation ------------------------- #
    if recommendation:
        with st.container(border=True):
            st.markdown("#### 🤖 Recommendation")

            rec_col1, rec_col2 = st.columns([2, 1])
            with rec_col1:
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

                if recommendation.get("next_actions"):
                    st.markdown("**Next Steps:**")
                    for na in recommendation["next_actions"]:
                        st.markdown(f"  📌 {na}")

            with rec_col2:
                st.metric("Score", f"{recommendation['score']:.1f}/100")
                bc = recommendation.get("baseline_comparison", {})
                if bc.get("improvement", 0) > 0:
                    st.metric("vs Baseline", f"+{bc['improvement']:.1f}", "improvement")

    # ------------------------- Save Simulation ------------------------- #
    _save_simulation(user_id, domain, horizon_months, scenarios, recommendation, params)


def _render_comparison_chart(scenarios: list, domain: str, horizon_months: int):
    fig = go.Figure()
    colors = ["#22d3ee", "#d946ef", "#fbbf24", "#34d399", "#fb7185", "#818cf8"]

    for i, s in enumerate(scenarios):
        color = colors[i % len(colors)]
        dash = "solid" if s.is_baseline else None
        width = 4 if s.is_baseline else 2.5

        if domain == "finance":
            x = [ts["month"] for ts in s.time_series]
            y = [ts["balance"] for ts in s.time_series]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines+markers",
                name=s.name,
                line=dict(color=color, width=width, dash=dash),
            ))
        elif domain == "study":
            x = [ts["month"] for ts in s.time_series]
            y = [ts["projected_score"] for ts in s.time_series]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines+markers",
                name=s.name,
                line=dict(color=color, width=width, dash=dash),
            ))
        elif domain == "habits":
            x = [ts["month"] for ts in s.time_series]
            y = [ts["projected_fitness_score"] for ts in s.time_series]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines+markers",
                name=s.name,
                line=dict(color=color, width=width, dash=dash),
            ))

    y_title = {
        "finance": "Projected Balance (₹)",
        "study": "Projected Score",
        "habits": "Projected Fitness Score",
    }.get(domain, "Value")

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", family="Inter, sans-serif"),
        xaxis=dict(
            title="Month", color="#cbd5e1",
            tickfont=dict(color="#cbd5e1"),
            title_font=dict(color="#cbd5e1"),
            gridcolor="rgba(255,255,255,0.06)",
        ),
        yaxis=dict(
            title=y_title, color="#cbd5e1",
            tickfont=dict(color="#cbd5e1"),
            title_font=dict(color="#cbd5e1"),
            gridcolor="rgba(255,255,255,0.06)",
        ),
        legend=dict(orientation="h", y=1.12, font=dict(color="#cbd5e1")),
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_time_series_charts(scenarios: list, domain: str, horizon_months: int):
    if domain == "finance":
        _render_finance_timeseries(scenarios)
    elif domain == "study":
        _render_study_timeseries(scenarios)
    elif domain == "habits":
        _render_habit_timeseries(scenarios)


def _render_finance_timeseries(scenarios: list):
    tabs = st.tabs([s.name for s in scenarios[:4]])
    for idx, (tab, scenario) in enumerate(zip(tabs, scenarios[:4])):
        with tab:
            if not scenario.time_series:
                st.caption("No data for this scenario.")
                continue
            df = pd.DataFrame(scenario.time_series)
            fig = ui.figure(280)
            fig.add_trace(go.Scatter(
                x=df["month"], y=df["balance"],
                mode="lines+markers", name="Balance",
                line=dict(color="#22d3ee", width=3),
            ))
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Balance (₹)",
                showlegend=False,
            )
            st.plotly_chart(
            fig,
                use_container_width=True,
                key=f"finance_timeseries_{idx}"
            )

            m = scenario.output_metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Final Balance", f"₹{m.get('final_balance', 0):,.0f}")
            c2.metric("Net Change", f"₹{m.get('net_worth_change', 0):,.0f}")
            c3.metric("Sustainable", "Yes" if m.get("sustainable") else "No")


def _render_study_timeseries(scenarios: list):
    tabs = st.tabs([s.name for s in scenarios[:4]])
    for idx, (tab, scenario) in enumerate(zip(tabs, scenarios[:4])):
        with tab:
            if not scenario.time_series:
                st.caption("No data for this scenario.")
                continue
            df = pd.DataFrame(scenario.time_series)
            fig = ui.figure(280)
            fig.add_trace(go.Scatter(
                x=df["month"], y=df["projected_score"],
                mode="lines+markers", name="Score",
                line=dict(color="#22d3ee", width=3),
            ))
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Projected Score",
                yaxis=dict(range=[0, 100]),
                showlegend=False,
            )
            st.plotly_chart(
            fig,
                 use_container_width=True,
                key=f"study_timeseries_{idx}"
            )  

            m = scenario.output_metrics
            c1, c2 = st.columns(2)
            c1.metric("Final Score", f"{m.get('final_score', 0):.1f}/100")
            c2.metric("Improvement", f"+{m.get('score_improvement', 0):.1f}")


def _render_habit_timeseries(scenarios: list):
    tabs = st.tabs([s.name for s in scenarios[:4]])
    for idx, (tab, scenario) in enumerate(zip(tabs, scenarios[:4])):
        with tab:
            if not scenario.time_series:
                st.caption("No data for this scenario.")
                continue
            df = pd.DataFrame(scenario.time_series)
            fig = ui.figure(280)
            fig.add_trace(go.Scatter(
                x=df["month"], y=df["projected_fitness_score"],
                mode="lines+markers", name="Fitness Score",
                line=dict(color="#22d3ee", width=3),
            ))
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Projected Fitness Score",
                yaxis=dict(range=[0, 100]),
                showlegend=False,
            )
            st.plotly_chart(
             fig,
                use_container_width=True,
                key=f"habit_timeseries_{idx}"
            )

            m = scenario.output_metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Fitness Score", f"{m.get('projected_fitness_score', 0):.1f}")
            c2.metric("Change", f"+{m.get('fitness_score_change', 0):.1f}")
            c3.metric("Exercise", f"{m.get('exercise_frequency', 0)} days/wk")


def _save_simulation(user_id: int, domain: str, horizon_months: int,
                     scenarios: list, recommendation: dict | None, params: dict):
    with st.expander("💾 Save Simulation Results"):
        title = st.text_input(
            "Simulation title",
            value=f"{domain.title()} Simulation - {horizon_months} months",
            key="sim_save_title",
        )
        if st.button("Save to Database", key="sim_save_btn", width="stretch"):
            try:
                sim_id = db.create_simulation(
                    user_id, domain, title, horizon_months,
                    parameters=params,
                )
                for s in scenarios:
                    scenario_id = db.add_simulation_scenario(
                        sim_id, s.name, s.is_baseline,
                        input_data=s.input_params,
                        output_data=s.output_metrics,
                        score=s.score,
                    )
                    if recommendation and s.name == recommendation.get("recommended_scenario"):
                        rec_scenario_id = scenario_id
                    else:
                        rec_scenario_id = None

                if recommendation and rec_scenario_id:
                    db.add_recommendation(
                        user_id, sim_id, rec_scenario_id,
                        recommendation_text=recommendation.get("reason", ""),
                        category=recommendation.get("category", domain),
                        priority=recommendation.get("priority", "medium"),
                        reason=recommendation.get("reason", ""),
                        risks="; ".join(recommendation.get("risks", [])),
                        next_action="; ".join(recommendation.get("next_actions", [])),
                    )

                flash(f"Simulation '{title}' saved successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not save simulation: {e}")
