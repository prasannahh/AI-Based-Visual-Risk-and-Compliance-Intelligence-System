"""
pages_app/study.py
Study & Productivity tab: CRUD on Study_Activities + Milestone 2
study/productivity intelligence (weekly hours chart & metrics).
"""

from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_bridge  # noqa: F401  (links the Milestone 2 AI Core Layer)

import database as db
from ai_models.common import streamlit_ui as ui
from ai_models.common.utils import get_or_train
from ai_models.study import model as study_model
from ai_models.study import predict as study_ai
from ai_models.study import train as study_train
from utils import flash, render_flash


def render():
    render_flash()

    user_id = st.session_state.user_id

    st.markdown("### 📚 Study & Productivity")

    # ------------------------- Forecasting ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📊 Weekly Study Hours")
        weekly = db.get_weekly_study_hours(user_id)
        study_df = db.get_study_activities(user_id)

        if weekly.empty or weekly["hours"].sum() == 0:
            st.caption("Log some study activities below to see your weekly pattern.")
        else:
            fig = go.Figure(
                go.Bar(x=weekly["day"], y=weekly["hours"], marker_color="#0891b2")
            )
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#000000", family="sans-serif"),
                xaxis=dict(color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
                yaxis=dict(color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig, width='stretch')

        peak_focus = db.get_peak_focus_time(user_id)
        avg_score = float(study_df["performance_score"].astype(float).mean()) if not study_df.empty else 0.0
        completion_rate = min(100.0, (weekly["hours"].sum() / 14.0 * 100)) if not weekly.empty else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Peak Focus Time", peak_focus)
        c2.metric("Completion Rate", f"{completion_rate:.0f}%")
        c3.metric("Average Score", f"{avg_score:.0f}")

    # ------------------------------ CRUD ------------------------------ #
    with st.container(border=True):
        st.markdown("#### ➕ Log Study Activity")
        with st.form("study_add_form"):
            subject = st.text_input("Subject")
            c1, c2 = st.columns(2)
            hours = c1.number_input("Hours logged", min_value=0.0, value=1.0, step=0.5)
            score = c2.number_input("Performance score (0-100)", min_value=0.0, max_value=100.0, value=75.0)
            sdate = st.date_input("Date", value=date.today())
            if st.form_submit_button("Save Entry", width='stretch'):
                if subject:
                    db.add_study_activity(user_id, subject, hours, score, sdate)
                    flash("Study activity saved.")
                    st.rerun()
                else:
                    flash("Please enter a subject.", "error")

    with st.container(border=True):
        st.markdown("#### 📋 Study Log")
        if study_df.empty:
            st.caption("No study activity yet.")
        else:
            display_df = study_df[["activity_id", "subject", "hours_logged", "performance_score", "date"]]
            edited = st.data_editor(
                display_df,
                width='stretch',
                hide_index=True,
                disabled=["activity_id"],
                column_config={
                    "activity_id": "ID",
                    "subject": "Subject",
                    "hours_logged": st.column_config.NumberColumn("Hours", format="%.1f"),
                    "performance_score": st.column_config.NumberColumn("Score", format="%.0f"),
                    "date": "Date",
                },
                num_rows="fixed",
                key="study_editor",
            )
            col_a, col_b = st.columns(2)
            if col_a.button("💾 Save Changes", key="study_save_changes"):
                for _, row in edited.iterrows():
                    db.update_study_activity(
                        int(row["activity_id"]),
                        subject=row["subject"],
                        hours_logged=float(row["hours_logged"]),
                        performance_score=float(row["performance_score"]),
                        date=row["date"],
                    )
                flash("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete an entry"):
                del_id = st.selectbox("Activity ID to delete", display_df["activity_id"].tolist())
                if st.button("Confirm Delete", key="study_delete_confirm"):
                    db.delete_study_activity(int(del_id))
                    flash("Entry deleted.", "info")
                    st.rerun()

    # ------------------------- AI Core (Milestone 2) ------------------------- #
    with st.container(border=True):
        st.markdown("#### 🤖 AI Study Assistant")
        ai_tab = st.tabs(
            ["Performance Prediction", "Weak Subject Detection", "Study Planner", "Time Optimisation", "Performance Trend", "Model Status"]
        )
        study_df = db.get_study_activities(user_id)

        # --------------------- Performance Prediction --------------------- #
        with ai_tab[0]:
            st.markdown("**Predict expected marks and GPA**")
            subject = st.selectbox("Subject", study_model.SUBJECTS, key="study_ai_subject")
            subj_scores = pd.to_numeric(study_df.loc[study_df["subject"] == subject, "performance_score"], errors="coerce").dropna() if not study_df.empty and "subject" in study_df.columns and "performance_score" in study_df.columns else pd.Series(dtype=float)
            prior = float(subj_scores.mean()) if not subj_scores.empty and not pd.isna(subj_scores.mean()) else 70.0
            c1, c2, c3 = st.columns(3)
            hours = c1.number_input("Hours to study", 0.0, 12.0, 2.0, 0.5, key="study_ai_hours")
            days_left = c2.number_input("Days to exam", 1, 180, 30, key="study_ai_days")
            consistency = c3.slider("Consistency (0-1)", 0.0, 1.0, 0.6, key="study_ai_consistency")
            st.caption(f"Prior average for {subject}: {prior:.0f}/100 (from your study log)")

            result = study_ai.predict_performance(subject, hours, int(days_left), consistency, prior)
            ui.render_metrics(
                {
                    "Expected Score": f"{result['predicted_score']:.1f}",
                    "Expected GPA": f"{result['predicted_gpa']:.2f}",
                    "Performance Band": result["band"],
                },
                columns=3,
            )

            model, _ = get_or_train("study", "performance_predictor", study_train.train_performance_model)
            sweep_hours = np.arange(0.0, 12.5, 0.5)
            sweep_frame = pd.DataFrame(
                [[subject, h, int(days_left), consistency, prior] for h in sweep_hours],
                columns=study_model.PERFORMANCE_FEATURES,
            )
            sweep_scores = np.clip(model.predict(sweep_frame), 0, 100)
            fig = ui.figure(300)
            fig.add_trace(
                go.Scatter(
                    x=sweep_hours, y=sweep_scores, mode="lines+markers",
                    name="Predicted score", line=dict(color=ui.ACCENT, width=3),
                    marker=dict(size=5),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[hours], y=[result["predicted_score"]], mode="markers",
                    name="Current selection", marker=dict(size=14, color="#d946ef"),
                )
            )
            fig.update_layout(
                xaxis_title="Hours to study",
                yaxis_title="Predicted score",
                xaxis=dict(color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
                yaxis=dict(range=[0, 100], color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
            )
            st.plotly_chart(fig, width='stretch')

            if st.button("💾 Log prediction", key="study_ai_predict_log"):
                ui.safe_log(
                    "study performance prediction",
                    db.log_study_prediction,
                    user_id, "performance_prediction",
                    result["predicted_score"], result["band"], confidence=1.0,
                    input_data={"subject": subject, "hours": hours, "days_to_exam": days_left, "consistency": consistency, "prior_score": prior},
                    output_data=result,
                )
                flash("Prediction logged to your history.")

        # -------------------- Weak Subject Detection -------------------- #
        with ai_tab[1]:
            st.markdown("**Subject-wise weakness ranking**")
            weak = study_ai.detect_weak_subjects(study_df)
            if not weak:
                st.caption("Log study activity (with performance scores) to detect weak subjects.")
            else:
                bar = ui.figure(280)
                bar.add_trace(go.Bar(x=[w["subject"] for w in weak], y=[w["avg_score"] for w in weak], marker_color=ui.ACCENT))
                st.plotly_chart(bar, width='stretch')

                display_weak = pd.DataFrame(weak)[["rank", "subject", "avg_score", "risk_score", "level", "trend"]]
                display_weak = display_weak.rename(
                    columns={
                        "rank": "Rank",
                        "subject": "Subject",
                        "avg_score": "Average Score",
                        "risk_score": "Risk Score",
                        "level": "Subject Level",
                        "trend": "Trend (%)",
                    }
                )
                st.dataframe(display_weak, hide_index=True, width='stretch')

                weakest = weak[0]
                st.warning(
                    f"Weakest area: **{weakest['subject']}** (Level: **{weakest['level']}**, Risk Score: **{weakest['risk_score']:.2f}**, Avg Score: **{weakest['avg_score']:.0f}/100**) — prioritise it in your planner."
                )
                ui.safe_log(
                    "weak subject detection",
                    db.log_study_prediction,
                    user_id, "weak_subject_detection",
                    weakest["avg_score"], weakest["subject"],
                    input_data={"subjects": [w["subject"] for w in weak]}, output_data=weak,
                )

        # ------------------------- Study Planner ------------------------- #
        with ai_tab[2]:
            st.markdown("**Generate a study timetable**")
            daily_hours = st.slider("Target study hours per day", 1.0, 10.0, 4.0, 0.5, key="study_ai_daily_hours")
            subjects_in_log = sorted(study_df["subject"].unique().tolist()) if not study_df.empty else []
            exam_dates = {}
            if subjects_in_log:
                with st.expander("Set upcoming exam dates"):
                    for subj in subjects_in_log:
                        exam_dates[subj] = st.date_input(f"{subj} exam", value=date.today().replace(year=date.today().year + 1), key=f"exam_{subj}")
            if st.button("Generate plan", type="primary", key="study_ai_plan"):
                plan = study_ai.generate_study_plan(study_df, exam_dates or None, daily_hours)
                st.markdown(f"**Priority subjects:** {', '.join(plan['priority_subjects']) if plan['priority_subjects'] else 'log study data first'}")
                if plan["revision_schedule"]:
                    st.markdown("**Revision schedule**")
                    st.dataframe(pd.DataFrame(plan["revision_schedule"]), hide_index=True, width='stretch')
                if plan["weekly_plan"]:
                    st.markdown("**Weekly plan**")
                    st.dataframe(pd.DataFrame(plan["weekly_plan"]), hide_index=True, width='stretch')
                if plan["daily_timetable"]:
                    st.markdown("**Daily timetable**")
                    st.dataframe(pd.DataFrame(plan["daily_timetable"]), hide_index=True, width='stretch')
                st.caption(" • ".join(plan["notes"]))
                ui.safe_log(
                    "study planner",
                    db.log_study_prediction,
                    user_id, "study_planner",
                    plan["total_study_hours"], "Weekly plan",
                    input_data={"daily_hours": daily_hours, "exam_dates": {k: str(v) for k, v in exam_dates.items()}},
                    output_data=plan,
                )

        # ----------------------- Time Optimisation ----------------------- #
        with ai_tab[3]:
            st.markdown("**Optimal study-hour allocation per subject**")
            total_hours = st.number_input("Weekly study hours to allocate", 1.0, 60.0, 12.0, 1.0, key="study_ai_total_hours")
            if st.button("Optimise", key="study_ai_optimise"):
                opt = study_ai.optimize_study_time(study_df, total_hours, {k: max((v - date.today()).days, 1) for k, v in exam_dates.items()} or None)
                if opt.empty:
                    st.caption("Log study data to optimise your time.")
                else:
                    bar = ui.figure(280)
                    bar.add_trace(go.Bar(x=opt["subject"], y=opt["recommended_hours"], marker_color=ui.ACCENT))
                    st.plotly_chart(bar, width='stretch')
                    st.dataframe(opt, hide_index=True, width='stretch')
                    ui.safe_log(
                        "study time optimisation",
                        db.log_study_prediction,
                        user_id, "time_optimisation",
                        float(opt["recommended_hours"].sum()), "Weekly allocation",
                        input_data={"total_hours": total_hours}, output_data=opt.to_dict("records"),
                    )

        # ---------------------- Performance Trend ---------------------- #
        with ai_tab[4]:
            st.markdown("**Forecast performance over time**")
            max_horizon = st.slider("Forecast horizon (days)", 30, 365, 90, step=15, key="study_trend_horizon")
            horizons = sorted({max_horizon // 3, (max_horizon * 2) // 3, max_horizon})
            trend = study_ai.predict_performance_trend(study_df, horizons=horizons)
            if trend.empty:
                st.caption("Log study activity with dates and scores to see your trend.")
            else:
                bar = ui.figure(280)
                bar.add_trace(go.Bar(x=trend["horizon_days"].astype(str) + " days", y=trend["predicted_score"], marker_color=ui.ACCENT))
                st.plotly_chart(bar, width='stretch')
                display_trend = trend.rename(
                    columns={
                        "horizon_days": "Forecast Horizon (days)",
                        "predicted_score": "Predicted Score",
                        "predicted_gpa": "Predicted GPA",
                    }
                )
                st.dataframe(display_trend, hide_index=True, width='stretch')
                ui.safe_log(
                    "performance trend",
                    db.log_study_prediction,
                    user_id, "performance_trend",
                    float(trend["predicted_score"].iloc[-1]), f"{max_horizon}-day forecast",
                    input_data={"horizons": trend["horizon_days"].tolist()}, output_data=trend.to_dict("records"),
                )

        # --------------------------- Model Status --------------------------- #
        with ai_tab[5]:
            ui.render_model_status("study")