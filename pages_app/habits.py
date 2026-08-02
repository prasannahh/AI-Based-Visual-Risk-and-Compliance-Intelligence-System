"""
pages_app/habits.py
Habit Tracker tab: CRUD on Habits + Milestone 2 habit predictions
(progress bars / trend insights for key habit categories).
"""

from datetime import date

import streamlit as st

import database as db

DEFAULT_HABIT_CATEGORIES = ["Exercise Frequency", "Sleep Schedule", "Reading Habit", "Meal Prep"]


def render():
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
                    st.success("Saved.")
                    st.rerun()
                else:
                    st.error("Please name the habit.")

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
                st.success("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete an entry"):
                del_id = st.selectbox("Habit ID to delete", display_df["habit_id"].tolist())
                if st.button("Confirm Delete", key="habit_delete_confirm"):
                    db.delete_habit(int(del_id))
                    st.rerun()
