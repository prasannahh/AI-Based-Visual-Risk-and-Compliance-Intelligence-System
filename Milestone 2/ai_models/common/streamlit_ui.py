"""
ai_models/common/streamlit_ui.py
Shared Streamlit rendering helpers for the AI Core Layer: theme-consistent
Plotly figures, model-status panels and resilient DB prediction logging.

Keeps the domain model code (ai_models/<domain>/*.py) free of any UI or
database imports so it stays unit-testable in isolation.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_models.common.utils import list_models

ACCENT = "#0891b2"


def figure(height: int = 300) -> go.Figure:
    """A Plotly figure pre-configured with the Digital Twin light theme and explicit black axis text."""
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#000000", family="sans-serif"),
        xaxis=dict(
            color="#000000",
            tickfont=dict(color="#000000"),
            title_font=dict(color="#000000"),
        ),
        yaxis=dict(
            color="#000000",
            tickfont=dict(color="#000000"),
            title_font=dict(color="#000000"),
        ),
        legend=dict(orientation="h", y=1.1, font=dict(color="#000000")),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
    )
    return fig


def safe_log(label: str, fn, *args, **kwargs) -> bool:
    """Run a DB logging call without letting failures break the UI.

    Returns True when the write succeeded.
    """
    try:
        fn(*args, **kwargs)
        return True
    except Exception as exc:  # pragma: no cover - DB layer may be unavailable
        st.warning(f"Could not store {label}: {exc}")
        return False


def render_model_status(domain: str) -> None:
    """Show the persisted models for a domain (auto-load/version info)."""
    models = list_models(domain)
    if not models:
        st.caption("No saved models yet — they are trained automatically the first time a prediction runs.")
        return
    rows = []
    for entry in models:
        metric = entry.get("metrics", {}) or {}
        score = metric.get("rmse", metric.get("f1", metric.get("r2")))
        rows.append(
            {
                "model": entry["name"],
                "version": entry["version"],
                "algorithm": metric.get("model", "—"),
                "best_metric": round(float(score), 3) if score is not None else "—",
                "records": entry.get("records", 0),
                "trained_at": entry.get("trained_at", "—"),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_metrics(metrics: dict[str, object], columns: int | None = None) -> None:
    """Render a mapping of label -> value as Streamlit metric cards."""
    items = list(metrics.items())
    if not items:
        return
    cols = st.columns(len(items) if not columns else columns)
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


def add_forecast_line(fig: go.Figure, dates, values, name: str, dash: str = None) -> None:
    """Append a (possibly dashed) forecast trace to a figure."""
    fig.add_trace(
        go.Scatter(
            x=dates, y=values, mode="lines+markers", name=name,
            line=dict(color=ACCENT, width=3, dash=dash),
        )
    )
