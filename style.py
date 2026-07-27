"""
style.py
--------
Custom CSS + reusable UI components: logo, header banner, footer, and a
subtle background pattern. Everything is self-contained in this one file
(the logo and background pattern are embedded as SVG/base64 strings) so
there are no extra image files to manage or paths to get wrong.

IMPORTANT: every HTML string passed to st.markdown(..., unsafe_allow_html=True)
is run through textwrap.dedent().strip() first. Without this, the leading
indentation that naturally appears when you write a multi-line string inside
a Python function can make Streamlit's markdown parser treat the block as a
*code block* instead of raw HTML (you'd see the literal tags on screen with
a copy-icon instead of a styled header/footer). Keep that pattern if you
add more HTML snippets here.

Usage in app.py:
    from style import inject_custom_css, hero_header, render_footer, risk_badge

    inject_custom_css()          # once, right after st.set_page_config(...)
    hero_header("Title", "Subtitle")   # top of a page
    render_footer()                    # bottom of a page
"""

import textwrap
import streamlit as st


PRIMARY = "#6C5CE7"
PRIMARY_DARK = "#4834D4"
ACCENT = "#00CEC9"
DANGER = "#FF6B6B"
WARNING = "#FDCB6E"
SUCCESS = "#00B894"
TEXT_DARK = "#1E1B2E"
BG_SOFT = "#F7F7FC"


def _md(html: str):
    """Dedent + strip, then render as raw HTML. Use for every HTML snippet."""
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Logo -- an original heartbeat-pulse badge in the app's brand colors.
# Inline SVG (not a file) so it always renders, no matter where the app runs.
# Written flush-left on purpose (no indentation) to avoid the code-block bug.
# ---------------------------------------------------------------------------
LOGO_SVG_LARGE = (
    '<svg width="42" height="42" viewBox="0 0 46 46" xmlns="http://www.w3.org/2000/svg">'
    '<defs><linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" stop-color="#6C5CE7"/><stop offset="100%" stop-color="#00CEC9"/>'
    '</linearGradient></defs>'
    '<circle cx="23" cy="23" r="22" fill="url(#logoGrad)"/>'
    '<circle cx="23" cy="23" r="22" fill="none" stroke="white" stroke-opacity="0.25" stroke-width="1.5"/>'
    '<path d="M8 24 h6 l3 -9 l4 18 l3 -13 l2.5 4 h11.5" fill="none" stroke="white" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="35" cy="12" r="2.6" fill="white"/></svg>'
)

LOGO_SVG_SMALL = LOGO_SVG_LARGE.replace('width="42" height="42"', 'width="20" height="20"')

# Subtle repeating background pattern (heartbeat line + dots), base64-encoded
# SVG, tiled at low opacity across the whole app background.
_BG_PATTERN_B64 = (
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiB2aWV3Qm94"
    "PSIwIDAgMTIwIDEyMCI+CiAgPGcgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNkM1Q0U3IiBzdHJva2Utd2lkdGg9IjEuNCIgb3Bh"
    "Y2l0eT0iMC4wNyI+CiAgICA8cGF0aCBkPSJNMTAgNjAgaDE4IGw2IC0yMiBsMTAgNDQgbDggLTMwIGw2IDggaDE4IiBzdHJv"
    "a2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KICAgIDxjaXJjbGUgY3g9Ijk1IiBjeT0iMjAi"
    "IHI9IjQiLz4KICAgIDxjaXJjbGUgY3g9IjIwIiBjeT0iMTAwIiByPSI0Ii8+CiAgPC9nPgo8L3N2Zz4K"
)


def inject_custom_css():
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        h1, h2, h3, .hero-title {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 700 !important;
        }}

        .stApp {{
            background-color: {BG_SOFT};
            background-image:
                linear-gradient(180deg, {BG_SOFT} 0%, #EFEFFB 100%),
                url("data:image/svg+xml;base64,{_BG_PATTERN_B64}");
            background-blend-mode: normal;
            background-repeat: repeat;
            background-size: auto, 120px 120px;
        }}

        .hero-banner {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            background: linear-gradient(120deg, {PRIMARY} 0%, {PRIMARY_DARK} 60%, {ACCENT} 130%);
            padding: 1.6rem 2rem;
            border-radius: 20px;
            color: white;
            margin-bottom: 1.6rem;
            box-shadow: 0 10px 30px rgba(108, 92, 231, 0.25);
        }}
        .hero-logo {{
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.12);
            border-radius: 14px;
            padding: 6px;
        }}
        .hero-text-block {{ display: flex; flex-direction: column; }}
        .hero-title {{
            font-size: 1.9rem;
            margin: 0;
            color: white !important;
            line-height: 1.15;
        }}
        .hero-subtitle {{
            font-size: 0.95rem;
            opacity: 0.9;
            margin-top: 0.25rem;
        }}

        .app-footer {{
            margin-top: 3rem;
            padding: 1.4rem 1.6rem;
            border-radius: 16px;
            background: white;
            border: 1px solid rgba(108, 92, 231, 0.08);
            box-shadow: 0 4px 16px rgba(30, 27, 46, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.6rem;
            color: {TEXT_DARK};
            font-size: 0.85rem;
        }}
        .app-footer .footer-brand {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
        }}
        .app-footer .footer-links a {{
            color: {PRIMARY_DARK};
            text-decoration: none;
            margin-left: 1rem;
            font-weight: 500;
        }}
        .app-footer .footer-links a:hover {{ text-decoration: underline; }}
        .app-footer .footer-disclaimer {{
            width: 100%;
            margin-top: 0.6rem;
            font-size: 0.75rem;
            opacity: 0.65;
        }}

        div[data-testid="stForm"], .custom-card {{
            background: white;
            border-radius: 16px;
            padding: 1.6rem 1.6rem 1rem 1.6rem;
            box-shadow: 0 4px 20px rgba(30, 27, 46, 0.06);
            border: 1px solid rgba(108, 92, 231, 0.08);
        }}

        div[data-testid="stMetric"] {{
            background: white;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            box-shadow: 0 2px 10px rgba(30, 27, 46, 0.05);
            border: 1px solid rgba(108, 92, 231, 0.08);
        }}
        div[data-testid="stMetricLabel"] {{
            font-weight: 600;
            color: {TEXT_DARK};
        }}

        .stButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(120deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.55rem 1.4rem;
            font-weight: 600;
            transition: all 0.15s ease-in-out;
            box-shadow: 0 4px 14px rgba(108, 92, 231, 0.35);
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(108, 92, 231, 0.45);
            color: white;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {PRIMARY_DARK} 0%, {PRIMARY} 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 0.4rem 0.6rem;
            margin-bottom: 0.3rem;
        }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
        .stTabs [data-baseweb="tab"] {{
            background: white;
            border-radius: 10px 10px 0 0;
            padding: 0.5rem 1rem;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.4rem;
        }}
        .badge-low {{ background: #D4F8E8; color: {SUCCESS}; }}
        .badge-medium {{ background: #FFF3D6; color: #B8860B; }}
        .badge-high {{ background: #FFE1E1; color: {DANGER}; }}
    </style>
    """
    st.markdown(textwrap.dedent(css), unsafe_allow_html=True)


def hero_header(title: str, subtitle: str = ""):
    """Top banner with logo + title + subtitle."""
    html = (
        f'<div class="hero-banner">'
        f'<div class="hero-logo">{LOGO_SVG_LARGE}</div>'
        f'<div class="hero-text-block">'
        f'<div class="hero-title">{title}</div>'
        f'<div class="hero-subtitle">{subtitle}</div>'
        f'</div></div>'
    )
    _md(html)


def render_footer():
    """Standard footer shown at the bottom of every page."""
    html = (
        f'<div class="app-footer">'
        f'<div class="footer-brand">{LOGO_SVG_SMALL} Health &amp; Fitness Digital Twin</div>'
        f'<div class="footer-links">'
        f'<a href="#" onclick="return false;">About</a>'
        f'<a href="#" onclick="return false;">Privacy</a>'
        f'<a href="#" onclick="return false;">Contact</a>'
        f'</div>'
        f'<div class="footer-disclaimer">'
        f'⚠️ Educational project. Predictions and risk scores are AI-generated estimates, '
        f'not medical advice — always consult a qualified professional for health decisions.'
        f'</div></div>'
    )
    _md(html)


def risk_badge(level: str) -> str:
    cls = {"Low": "badge-low", "Medium": "badge-medium", "High": "badge-high"}.get(level, "badge-medium")
    return f'<span class="badge {cls}">{level}</span>'