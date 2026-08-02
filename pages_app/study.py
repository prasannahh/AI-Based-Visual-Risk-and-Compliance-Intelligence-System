"""
pages_app/study.py
Study & Productivity tab: CRUD on Study_Activities + Milestone 2
study/productivity intelligence (weekly hours chart & metrics).
"""

from datetime import date

import plotly.graph_objects as go
import streamlit as st

import database as db


def render():
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
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

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
            if st.form_submit_button("Save Entry", use_container_width=True):
                if subject:
                    db.add_study_activity(user_id, subject, hours, score, sdate)
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error("Please enter a subject.")

    with st.container(border=True):
        st.markdown("#### 📋 Study Log")
        if study_df.empty:
            st.caption("No study activity yet.")
        else:
            display_df = study_df[["activity_id", "subject", "hours_logged", "performance_score", "date"]]
            edited = st.data_editor(
                display_df,
                use_container_width=True,
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
                st.success("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete an entry"):
                del_id = st.selectbox("Activity ID to delete", display_df["activity_id"].tolist())
                if st.button("Confirm Delete", key="study_delete_confirm"):
                    db.delete_study_activity(int(del_id))
                    st.rerun()