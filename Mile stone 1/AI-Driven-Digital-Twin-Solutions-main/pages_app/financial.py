"""
pages_app/financial.py
Financial Analyst tab: CRUD on Financial_Records + Milestone 2
financial forecasting (savings projection chart & metrics).
"""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_bridge  # noqa: F401  (links the Milestone 2 AI Core Layer)

import database as db
from ai_models.common import streamlit_ui as ui
from ai_models.finance import predict as fin_ai
from utils import flash, render_flash


def render():
    render_flash()

    user_id = st.session_state.user_id

    st.markdown("### 💰 Financial Analyst")

    # ------------------------- Forecasting ------------------------- #
    with st.container(border=True):
        st.markdown("#### 📈 Savings Projection")
        history, projected_1yr, monthly_rate = db.get_savings_forecast(user_id)

        horizon_months = 12
        extra_savings = 0.0
        current_savings = 0.0
        projected = 0.0
        effective_rate = 0.0

        if history.empty:
            st.caption("Add some financial records below to generate a forecast.")
        else:
            c_h, c_e = st.columns(2)
            horizon_months = c_h.slider("Forecast horizon (months)", 1, 36, 12, key="fin_proj_months")
            extra_savings = c_e.number_input("Additional monthly savings (₹)", 0.0, 1000000.0, 0.0, 500.0, key="fin_proj_extra")
            effective_rate = monthly_rate + extra_savings
            last_date = history["date"].iloc[-1]
            last_val = history["cumulative_savings"].iloc[-1]
            current_savings = last_val
            future_dates = [last_date + pd.Timedelta(days=30 * m) for m in range(1, horizon_months + 1)]
            future_vals = [last_val + effective_rate * m for m in range(1, horizon_months + 1)]
            projected = future_vals[-1]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=history["date"], y=history["cumulative_savings"],
                    mode="lines+markers", name="Actual",
                    line=dict(color="#0891b2", width=3),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[last_date] + future_dates, y=[last_val] + future_vals,
                    mode="lines+markers", name="Projected",
                    line=dict(color="#d946ef", width=2, dash="dash"),
                )
            )
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#000000", family="sans-serif"),
                xaxis=dict(color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
                yaxis=dict(color="#000000", tickfont=dict(color="#000000"), title_font=dict(color="#000000")),
                legend=dict(orientation="h", y=1.1, font=dict(color="#000000")),
                margin=dict(l=10, r=10, t=10, b=10),
                height=340,
            )
            st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Current Savings", f"₹{current_savings:,.0f}")
        c2.metric(f"Projected ({horizon_months} mo)", f"₹{projected:,.0f}")
        c3.metric("Savings Rate", f"₹{effective_rate:,.0f} / mo")

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
                flash("Financial record saved.")
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
                flash("Changes saved.")
                st.rerun()
            with col_b.popover("🗑️ Delete a record"):
                del_id = st.selectbox("Record ID to delete", display_df["record_id"].tolist())
                if st.button("Confirm Delete", key="fin_delete_confirm"):
                    db.delete_financial_record(int(del_id))
                    flash("Record deleted.", "info")
                    st.rerun()

    # ------------------------- AI Core (Milestone 2) ------------------------- #
    with st.container(border=True):
        st.markdown("#### 🤖 AI Financial Assistant")
        ai_tab = st.tabs(
            ["Expense Classification", "Spending Analysis", "Savings Prediction", "Budget Recommendation", "Balance Forecast", "Model Status"]
        )
        records = db.get_financial_records(user_id)

        # ---------------------- Expense Classification ---------------------- #
        with ai_tab[0]:
            st.markdown("**Classify an expense automatically**")
            with st.form("expense_classify_form"):
                description = st.text_input("Transaction description", placeholder="e.g. 'swiggy dinner' or 'electricity bill'")
                if st.form_submit_button("Classify", use_container_width=True):
                    if not description:
                        st.error("Please enter a transaction description.")
                    else:
                        result = fin_ai.classify_expense(description)
                        st.success(f"Category: **{result['category']}** (confidence {result['confidence'] * 100:.0f}%)")
                        ui.safe_log(
                            "expense classification",
                            db.log_finance_prediction,
                            user_id, "expense_classification",
                            None, result["category"], confidence=result["confidence"],
                            input_data={"description": description}, output_data=result,
                        )
                        ui.safe_log(
                            "expense prediction trace",
                            db.log_prediction,
                            user_id, "finance", "expense_classifier",
                            result, confidence=result["confidence"], input_data={"description": description},
                        )

        # ----------------------- Spending Analysis ----------------------- #
        with ai_tab[1]:
            analysis = fin_ai.spending_analysis(records)
            if analysis["category_wise"].empty:
                st.caption("Log some expenses (type = Expense) to see your spending patterns.")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Total spent", f"₹{analysis['total_spent']:,.0f}")
                with c2:
                    top = analysis["category_wise"].iloc[0]
                    st.metric("Top category", f"{top['category']} · ₹{top['spent']:,.0f}")

                pie = ui.figure(320)
                pie.add_trace(
                    go.Pie(
                        labels=analysis["category_wise"]["category"],
                        values=analysis["category_wise"]["spent"],
                        hole=0.4,
                        textinfo="label+percent",
                        textfont=dict(color="#000000", size=12),
                        insidetextfont=dict(color="#000000", size=12),
                        outsidetextfont=dict(color="#000000", size=12),
                    )
                )
                pie.update_layout(
                    font=dict(color="#000000"),
                    legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center", font=dict(color="#000000")),
                    margin=dict(l=20, r=20, t=20, b=40),
                )
                st.plotly_chart(pie, use_container_width=True)
                st.dataframe(
                    analysis["category_wise"].rename(columns={"category": "Spending Reason / Category", "spent": "Amount Spent (₹)"}),
                    hide_index=True,
                    use_container_width=True,
                )

                if not analysis["monthly"].empty:
                    st.markdown("##### 📅 Monthly Spending Breakdown")
                    formatted_months = []
                    for m in analysis["monthly"]["month"]:
                        try:
                            formatted_months.append(pd.Period(str(m)).strftime("%b %Y"))
                        except Exception:
                            formatted_months.append(str(m))

                    monthly = ui.figure(280)
                    monthly.add_trace(
                        go.Bar(
                            x=formatted_months,
                            y=analysis["monthly"]["spent"],
                            marker_color="#0891b2",
                            text=[f"₹{val:,.0f}" for val in analysis["monthly"]["spent"]],
                            textposition="auto",
                            textfont=dict(color="#000000"),
                        )
                    )
                    monthly.update_layout(
                        font=dict(color="#000000"),
                        xaxis=dict(
                            type="category",
                            title="Month",
                            color="#000000",
                            tickfont=dict(color="#000000"),
                            title_font=dict(color="#000000"),
                        ),
                        yaxis=dict(
                            title="Total Spent (₹)",
                            color="#000000",
                            tickfont=dict(color="#000000"),
                            title_font=dict(color="#000000"),
                        ),
                        margin=dict(l=20, r=20, t=20, b=30),
                    )
                    st.plotly_chart(monthly, use_container_width=True)

                ui.safe_log(
                    "spending analysis",
                    db.log_finance_prediction,
                    user_id, "spending_analysis",
                    analysis["total_spent"], "Monthly breakdown",
                    input_data={"records": len(records)}, output_data={"total_spent": analysis["total_spent"]},
                )

        # ----------------------- Savings Prediction ----------------------- #
        with ai_tab[2]:
            st.markdown("**Forecast cumulative savings**")
            max_months = st.slider("Forecast horizon (months)", 3, 24, 12, key="fin_sav_months")
            savings_forecast = fin_ai.predict_savings(records, horizons=tuple(range(1, max_months + 1)))
            if savings_forecast.empty:
                st.caption("Add income and savings records to generate a forecast.")
            else:
                bar = ui.figure(300)
                bar.add_trace(
                    go.Bar(
                        x=savings_forecast["months_ahead"].astype(str) + " mo",
                        y=savings_forecast["predicted_savings"],
                        marker_color="#0891b2",
                        text=[f"₹{val:,.0f}" for val in savings_forecast["predicted_savings"]],
                        textposition="auto",
                        textfont=dict(color="#000000"),
                    )
                )
                bar.update_layout(
                    font=dict(color="#000000"),
                    xaxis=dict(
                        type="category",
                        title="Horizon",
                        color="#000000",
                        tickfont=dict(color="#000000"),
                        title_font=dict(color="#000000"),
                    ),
                    yaxis=dict(
                        title="Predicted Savings (₹)",
                        color="#000000",
                        tickfont=dict(color="#000000"),
                        title_font=dict(color="#000000"),
                    ),
                    margin=dict(l=20, r=20, t=20, b=30),
                )
                st.plotly_chart(bar, use_container_width=True)
                st.dataframe(savings_forecast, hide_index=True, use_container_width=True)
                ui.safe_log(
                    "savings prediction",
                    db.log_finance_prediction,
                    user_id, "savings_prediction",
                    float(savings_forecast["predicted_savings"].iloc[-1]), f"{max_months}-month forecast",
                    input_data={"horizon_months": savings_forecast["months_ahead"].tolist()},
                    output_data=savings_forecast.to_dict("records"),
                )

        # -------------------- Budget Recommendation -------------------- #
        with ai_tab[3]:
            budget = fin_ai.recommend_budget(records)
            st.caption(budget["basis"])
            ui.render_metrics(
                {
                    "Monthly budget": f"₹{budget['monthly_budget']:,.0f}",
                    "Weekly budget": f"₹{budget['weekly_budget']:,.0f}",
                    "Emergency fund": f"₹{budget['emergency_fund']:,.0f}",
                    "Savings goal": f"₹{budget['savings_goal']:,.0f}",
                },
                columns=4,
            )
            if not budget["category_limits"].empty:
                st.markdown("**Category-wise budget limits**")
                st.dataframe(budget["category_limits"], hide_index=True, use_container_width=True)
            ui.safe_log(
                "budget recommendation",
                db.log_finance_prediction,
                user_id, "budget_recommendation",
                budget["monthly_budget"], "Monthly budget",
                input_data={"records": len(records)}, output_data=budget,
            )

        # --------------------- Future Balance Forecast --------------------- #
        with ai_tab[4]:
            st.markdown("**Project account balance**")
            days = st.slider("Forecast horizon (days)", 30, 365, 90, key="fin_balance_days")
            if records.empty:
                st.info("Savings prediction unavailable.\nRun the Savings Prediction model first.")
            else:
                balance = fin_ai.predict_future_balance(records, days=days)
                if balance.empty:
                    st.info("Savings prediction unavailable.\nRun the Savings Prediction model first.")
                else:
                    line = ui.figure(320)
                    line.add_trace(
                        go.Scatter(
                            x=balance["date"],
                            y=balance["predicted_balance"],
                            mode="lines+markers",
                            name="Projected Balance",
                            line=dict(color=ui.ACCENT, width=3),
                        )
                    )
                    st.plotly_chart(line, use_container_width=True)
                    projected_val = balance["predicted_balance"].iloc[-1]
                    st.metric("Projected balance", f"₹{projected_val:,.0f}")
                    ui.safe_log(
                        "balance forecast",
                        db.log_finance_prediction,
                        user_id,
                        "future_balance",
                        float(projected_val),
                        f"{days}-day forecast",
                        input_data={"days": days},
                        output_data=balance.head(30).to_dict("records"),
                    )

        # --------------------------- Model Status --------------------------- #
        with ai_tab[5]:
            ui.render_model_status("finance")