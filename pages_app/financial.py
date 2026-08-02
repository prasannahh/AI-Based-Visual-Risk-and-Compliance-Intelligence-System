"""
pages_app/financial.py
Financial Analyst tab: CRUD on Financial_Records + Milestone 2
financial forecasting (savings projection chart & metrics).
"""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import database as db


def render():
    user_id = st.session_state.user_id

    st.markdown("### 💰 Financial Analyst")

    # ------------------------- Forecasting ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📈 Savings Projection")
        history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)

        if history.empty:
            st.caption("Add some financial records below to generate a forecast.")
        else:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=history["date"], y=history["cumulative_savings"],
                    mode="lines+markers", name="Actual",
                    line=dict(color="#0891b2", width=3),
                )
            )
            if len(history) >= 2:
                last_date = history["date"].iloc[-1]
                last_val = history["cumulative_savings"].iloc[-1]
                future_date = last_date + pd.Timedelta(days=365)
                fig.add_trace(
                    go.Scatter(
                        x=[last_date, future_date], y=[last_val, projected_1yr],
                        mode="lines+markers", name="Projected",
                        line=dict(color="#d946ef", width=2, dash="dash"),
                    )
                )

            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=10, r=10, t=10, b=10),
                height=340,
            )
            st.plotly_chart(fig, use_container_width=True)

        current_savings = float(history["cumulative_savings"].iloc[-1]) if not history.empty else 0.0
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Savings", f"₹{current_savings:,.0f}")
        c2.metric("Projected (1 Year)", f"₹{projected_1yr:,.0f}")
        c3.metric("Savings Rate", f"₹{monthly_rate:,.0f} / mo")

    # ------------------------------ CRUD ------------------------------ #
    with st.container(border=True):
        st.markdown("#### ➕ Add Financial Record")
        with st.form("fin_add_form"):
            c1, c2, c3 = st.columns(3)
            category = c1.selectbox("Category", ["Housing", "Food", "Dining Out", "Transport", "Salary", "Investment", "Entertainment", "Other"])
            ttype = c2.selectbox("Type", ["Income", "Expense", "Savings"])
            amount = c3.number_input("Amount", min_value=0.0, value=0.0)
            fdate = st.date_input("Date", value=date.today())
            if st.form_submit_button("Save Entry", use_container_width=True):
                db.add_financial_record(user_id, category, amount, ttype, fdate)
                st.success("Saved.")
                st.rerun()

    with st.container(border=True):
        st.markdown("#### 📋 Your Financial Records")
        records = db.get_financial_records(user_id)
        if records.empty:
            st.caption("No records yet.")
        else:
            display_df = records[["record_id", "category", "amount", "transaction_type", "date"]]
            edited = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                disabled=["record_id"],
                column_config={
                    "record_id": "ID",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                    "transaction_type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense", "Savings"]),
                    "date": "Date",
                },
                num_rows="fixed",
                key="fin_editor",
            )
            col_a, col_b = st.columns(2)
            if col_a.button("💾 Save Changes", key="fin_save_changes"):
                for _, row in edited.iterrows():
                    db.update_financial_record(
                        int(row["record_id"]),
                        category=row["category"],
                        amount=float(row["amount"]),
                        transaction_type=row["transaction_type"],
                        date=row["date"],
                    )
                st.success("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete a record"):
                del_id = st.selectbox("Record ID to delete", display_df["record_id"].tolist())
                if st.button("Confirm Delete", key="fin_delete_confirm"):
                    db.delete_financial_record(int(del_id))
                    st.rerun()