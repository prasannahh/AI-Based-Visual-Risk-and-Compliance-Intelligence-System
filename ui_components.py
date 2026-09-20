"""
ui_components.py
Shared, reusable UI pieces: global header, global footer (with popovers,
centered copyright), and the user info/stats block (no avatar image).
"""

import streamlit as st

from utils import APP_TITLE

ABOUT_TEXT = """
<div class="dt-popover-body">
<div class="dt-popover-title">🧬 About Digital Twin AI</div>
<p>Digital Twin AI builds a living digital representation of your finances,
study habits, and daily routines — then uses predictive analytics to help
you make better decisions <i>before</i> you make them in real life.</p>
<ul>
<li>📊 <b>Milestone 1</b> — data collection &amp; profiling</li>
<li>🔮 <b>Milestone 2</b> — forecasting &amp; predictive analytics</li>
<li>🚀 Built with Streamlit + PostgreSQL</li>
</ul>
</div>
"""

PRIVACY_TEXT = """
<div class="dt-popover-body">
<div class="dt-popover-title">🔒 Privacy & Security</div>
<ul>
<li>🗄️ Data stored in your own PostgreSQL database</li>
<li>🚫 Never shared with third parties</li>
<li>🔑 Passwords hashed with salted PBKDF2-SHA256, never stored in plain text</li>
<li>📄 Placeholder policy text for demo purposes</li>
</ul>
</div>
"""

CONTACT_TEXT = """
<div class="dt-popover-body">
<div class="dt-popover-title">💬 Need Help?</div>
<p>We'd love to hear from you.</p>
<ul>
<li>📧 support@digitaltwin.ai</li>
<li>🗨️ In-app feedback — coming soon</li>
<li>⏱️ Typical response time: 1–2 business days</li>
</ul>
<p style="color:#93a4bd;font-size:0.8rem;">Placeholder contact info for demo purposes.</p>
</div>
"""


def render_header():
    st.markdown(
        f"""
        <div class="dt-header-wrap">
            <div class="dt-header-eyebrow">AI-Powered Decision Intelligence</div>
            <div class="dt-header-title">🧬 Digital Twin AI</div>
            <div class="dt-header-sub">Personal Life Simulation &amp; Decision Assistant · Simulate · Optimize · Evolve</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    with st.container(key="app_footer"):
        # Copyright text centered exactly in the middle of the footer
        st.markdown(
            "<div class='dt-footer-copy'>© 2026 Digital Twin AI Solutions · All Rights Reserved</div>",
            unsafe_allow_html=True,
        )
        _, c2, c3, c4, _ = st.columns([3, 1, 1, 1, 3])
        with c2:
            with st.popover("About"):
                st.markdown(ABOUT_TEXT, unsafe_allow_html=True)
        with c3:
            with st.popover("Privacy"):
                st.markdown(PRIVACY_TEXT, unsafe_allow_html=True)
        with c4:
            with st.popover("Contact"):
                st.markdown(CONTACT_TEXT, unsafe_allow_html=True)


def render_avatar_block(user: dict, days_active: int, goal_score: float):
    """User name + quick stats, used on Dashboard / Profile pages.
    No avatar image - just the name, occupation, and key metrics."""
    st.markdown(f"### {user.get('name', 'User')}")
    st.caption(user.get("occupation") or "—")
    s1, s2, s3 = st.columns(3)
    s1.metric("Age", user.get("age") or "—")
    s2.metric("Goal Score", f"{goal_score:.0f}%")
    s3.metric("Days Active", days_active)