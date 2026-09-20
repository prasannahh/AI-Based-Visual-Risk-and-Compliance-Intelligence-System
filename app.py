"""
app.py
Entry point for Digital Twin AI - Personal Life Simulation & Decision Assistant.

Run with:
    streamlit run app.py

Requires a running PostgreSQL server with a database named `digital_twin`
(see README.md for setup). Tables are created automatically on first run.
"""

import ai_bridge  # noqa: F401  (links the Milestone 2 AI Core Layer)

from datetime import datetime

import streamlit as st

import database as db
from auth import render_auth
from ui_components import render_footer, render_header
from utils import (
    APP_TITLE,
    init_session_state,
    inject_theme,
    logout,
    restore_session,
    sync_cookie_auth,
)

st.set_page_config(page_title=APP_TITLE, page_icon="🧬", layout="wide")

init_session_state()
restore_session()
sync_cookie_auth()
inject_theme()

# --------------------------------------------------------------------------- #
# Database bootstrap
# --------------------------------------------------------------------------- #
try:
    db.init_db()
    _db_ok = True
except Exception as e:
    _db_ok = False
    _db_error = str(e)

render_header()

if not _db_ok:
    st.error(
        "Could not connect to PostgreSQL database `digital_twin`. "
        "Check your connection settings in `.streamlit/secrets.toml` or "
        "environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)."
    )
    st.code(_db_error)
    st.stop()

# --------------------------------------------------------------------------- #
# Stale-session guard: if the logged-in user no longer exists in the database,
# drop the session gracefully instead of crashing every page with a None user.
# --------------------------------------------------------------------------- #
if st.session_state.logged_in:
    _current_user = db.get_user(st.session_state.user_id)
    if _current_user is None:
        logout()

# --------------------------------------------------------------------------- #
# Auth gate
# --------------------------------------------------------------------------- #
if not st.session_state.logged_in:
    render_auth()
    render_footer()
    st.stop()

# --------------------------------------------------------------------------- #
# Sidebar navigation
# --------------------------------------------------------------------------- #
NAV_ITEMS = {
    "Dashboard": "🏠",
    "Personal Data & Profile": "🧑\u200d💼",
    "Financial Analyst": "💰",
    "Study & Productivity": "📚",
    "Habit Tracker": "✅",
    "Digital Twin Simulation": "🧬",
    "Conversational AI": "💬",
}

with st.sidebar:
    st.markdown(
        f"""
        <div class="dt-sb-brand">
            <div class="dt-sb-logo">🧬</div>
            <div class="dt-sb-title">Digital Twin AI</div>
            <div class="dt-sb-sub">Decision Intelligence</div>
        </div>
        <div class="dt-sb-user">
            <div class="dt-sb-user-label">Signed in as</div>
            <div class="dt-sb-user-name">{st.session_state.user_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    jwt_exp = st.session_state.get("jwt_exp")
    if jwt_exp:
        st.caption(f"Session expires {datetime.fromtimestamp(int(jwt_exp)).strftime('%d %b %Y, %H:%M')}")
    st.divider()

    choice = st.radio(
        "Navigate",
        list(NAV_ITEMS.keys()),
        format_func=lambda p: f"{NAV_ITEMS[p]}  {p}",
        index=list(NAV_ITEMS.keys()).index(st.session_state.page)
        if st.session_state.page in NAV_ITEMS else 0,
        label_visibility="collapsed",
    )
    st.session_state.page = choice

    st.divider()
    if st.button("🚪 Log Out", width='stretch'):
        logout()
        st.rerun()

# --------------------------------------------------------------------------- #
# Page routing
# --------------------------------------------------------------------------- #
if st.session_state.page == "Dashboard":
    from pages_app import dashboard
    dashboard.render()
elif st.session_state.page == "Personal Data & Profile":
    from pages_app import profile
    profile.render()
elif st.session_state.page == "Financial Analyst":
    from pages_app import financial
    financial.render()
elif st.session_state.page == "Study & Productivity":
    from pages_app import study
    study.render()
elif st.session_state.page == "Habit Tracker":
    from pages_app import habits
    habits.render()
elif st.session_state.page == "Digital Twin Simulation":
    from pages_app import simulation
    simulation.render()
elif st.session_state.page == "Conversational AI":
    from pages_app import ai_chat
    ai_chat.render()

render_footer()
