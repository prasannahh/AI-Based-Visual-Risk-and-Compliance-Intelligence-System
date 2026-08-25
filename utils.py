"""
utils.py
Premium DARK GLASS theme (deep navy / glass cards / cyan-gold accents),
password hashing, JWT auth tokens, and session-state helpers.
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
import time

import streamlit as st
import streamlit.components.v1 as components

APP_TITLE = "Digital Twin AI - Personal Life Simulation & Decision Assistant"

# --------------------------------------------------------------------------- #
# Password hashing (PBKDF2-SHA256, no extra dependency required)
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return binascii.hexlify(salt).decode() + ":" + binascii.hexlify(dk).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = binascii.unhexlify(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return binascii.hexlify(dk).decode() == hash_hex
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "user_gender": None,
        "page": "Dashboard",
        "auth_mode": "Login",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def logout():
    for k in ["logged_in", "user_id", "user_name", "user_gender"]:
        st.session_state[k] = False if k == "logged_in" else None
    st.session_state["page"] = "Dashboard"
    st.session_state["auth_mode"] = "Login"
    st.session_state.pop("jwt_token", None)
    st.session_state.pop("jwt_exp", None)
    try:
        if "auth" in st.query_params:
            st.query_params.pop("auth")
    except Exception:
        pass
    st.session_state["_clear_cookie"] = True


# --------------------------------------------------------------------------- #
# JWT auth tokens (HMAC-SHA256 / HS256, stdlib only - no PyJWT dependency)
#
# On login a signed token is minted and stored in session_state. On every run
# the token's signature + expiry are re-validated, so a stale/expired token
# automatically logs the user out.
# --------------------------------------------------------------------------- #
_JWT_SECRET = os.getenv("JWT_SECRET", "digital-twin-dev-secret-change-me")
_JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def create_token(payload: dict, expires_hours: int | None = None) -> str:
    """Mint a signed HS256 JWT containing the given claims + iat/exp."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = dict(payload)
    body["iat"] = now
    body["exp"] = now + (expires_hours or _JWT_EXPIRES_HOURS) * 3600

    head = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    claims = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{head}.{claims}".encode("utf-8")
    sig = _b64url_encode(hmac.new(_JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest())
    return f"{head}.{claims}.{sig}"


def validate_token(token: str) -> dict | None:
    """Verify signature and expiry. Returns the claims dict or None."""
    try:
        head, claims, sig = token.split(".")
        signing_input = f"{head}.{claims}".encode("utf-8")
        expected = _b64url_encode(hmac.new(_JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, sig):
            return None
        body = json.loads(_b64url_decode(claims))
        if int(body.get("exp", 0)) < int(time.time()):
            return None
        return body
    except Exception:
        return None


def restore_session() -> bool:
    """Re-hydrate the logged-in session from session_state (or an explicit
    ?auth= link token).

    Login is intentionally NOT persisted in a browser cookie: a stale cookie
    used to auto-log-in the previously signed-in user, skipping the login
    screen and making new registrations look like they never happened. Every
    fresh browser session now starts at the login screen."""
    if st.session_state.get("_clear_cookie"):
        return False

    token = st.session_state.get("jwt_token")
    if not token:
        token = st.query_params.get("auth")
        if isinstance(token, list):
            token = token[0] if token else None

    if not token:
        return False

    payload = validate_token(token)
    if payload is None:
        logout()
        return False

    was_logged_in = bool(st.session_state.get("logged_in"))
    st.session_state.jwt_token = token
    st.session_state.jwt_exp = payload.get("exp")
    st.session_state.logged_in = True
    st.session_state.user_id = payload.get("user_id")
    st.session_state.user_name = payload.get("name")
    st.session_state.user_gender = payload.get("gender")
    if not was_logged_in:
        st.session_state.page = "Dashboard"

    # Keep URL clean: remove auth query parameter if present
    try:
        if "auth" in st.query_params:
            st.query_params.pop("auth")
    except Exception:
        pass

    return True


def restore_session_from_token() -> bool:
    return restore_session()


def restore_session_from_query() -> bool:
    return restore_session()


def sync_cookie_auth() -> None:
    """Clear any previously stored auth cookie / localStorage.

    Auth is kept only in session_state, so each fresh browser session starts
    on the login screen instead of auto-logging-in as the previous user."""
    st.session_state.pop("_clear_cookie", None)
    components.html(
        "<script>"
        "document.cookie = 'dt_jwt=; path=/; max-age=0; SameSite=Lax';"
        "try { window.parent.document.cookie = 'dt_jwt=; path=/; max-age=0; SameSite=Lax'; } catch(e){}"
        "try { window.parent.localStorage.removeItem('dt_jwt'); } catch(e){}"
        "</script>",
        height=0,
    )


def flash(message: str, level: str = "success") -> None:
    """Queue a one-shot notification that survives st.rerun().

    st.success() followed by st.rerun() gets wiped out by the rerun, so the
    user never sees a "saved" message. Store it in session state instead and
    let render_flash() display it on the next run.
    """
    st.session_state["_flash"] = {"message": message, "level": level}


def render_flash() -> None:
    """Display (once) any queued flash notification as a toast + banner."""
    msg = st.session_state.pop("_flash", None)
    if not msg:
        return
    st.toast(msg["message"])
    if msg["level"] == "success":
        st.success(msg["message"])
    elif msg["level"] == "error":
        st.error(msg["message"])
    elif msg["level"] == "warning":
        st.warning(msg["message"])
    else:
        st.info(msg["message"])


# --------------------------------------------------------------------------- #
# Theme CSS - PREMIUM DARK GLASS theme: deep navy canvas, frosted-glass cards,
# cyan gradient accents, gold highlights. Every selector pairs a background
# with a text color so nothing becomes unreadable in dark mode.
# --------------------------------------------------------------------------- #
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --dt-bg-0: #05070d;
    --dt-bg-1: #0a101c;
    --dt-bg-2: #0d1626;
    --dt-card: rgba(255, 255, 255, 0.045);
    --dt-card-strong: rgba(255, 255, 255, 0.075);
    --dt-border: rgba(255, 255, 255, 0.10);
    --dt-border-strong: rgba(255, 255, 255, 0.19);
    --dt-accent: #22d3ee;
    --dt-accent-2: #38bdf8;
    --dt-accent-3: #818cf8;
    --dt-gold: #fbbf24;
    --dt-text: #e8eef7;
    --dt-text-muted: #93a4bd;
    --dt-danger: #fb7185;
    --dt-success: #34d399;
    --dt-input-bg: rgba(255, 255, 255, 0.06);
    --dt-input-text: #e8eef7;
    --dt-placeholder: #64748b;
}

/* ------------------------------ App canvas ------------------------------ */
.stApp {
    color-scheme: dark;
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
    background:
        radial-gradient(1100px 620px at 12% -8%, rgba(34, 211, 238, 0.13), transparent 55%),
        radial-gradient(900px 520px at 108% -6%, rgba(129, 140, 248, 0.12), transparent 55%),
        radial-gradient(950px 720px at 50% 122%, rgba(6, 182, 212, 0.07), transparent 60%),
        linear-gradient(165deg, #05070d 0%, #0a101c 52%, #070b15 100%);
    color: var(--dt-text);
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp li {
    color: var(--dt-text);
}

/* Custom scrollbars */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.14); border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.26); }

/* Native Streamlit top toolbar -> translucent dark bar */
header[data-testid="stHeader"] {
    background-color: rgba(5, 7, 13, 0.55) !important;
    backdrop-filter: blur(12px);
    box-shadow: none !important;
    border-bottom: 1px solid var(--dt-border);
}
header[data-testid="stHeader"] * { color: var(--dt-text) !important; }
div[data-testid="stDecoration"] { display: none; }

/* -------------------------------- Header -------------------------------- */
.dt-header-wrap {
    text-align: center;
    padding: 1.3rem 0 1.7rem 0;
    position: relative;
}
.dt-header-eyebrow {
    font-size: 0.66rem;
    letter-spacing: 0.44em;
    text-transform: uppercase;
    color: var(--dt-accent);
    font-weight: 700;
    margin-bottom: 0.45rem;
    opacity: 0.9;
}
.dt-header-title {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(92deg, #22d3ee 0%, #60a5fa 48%, #c084fc 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
    line-height: 1.15;
}
.dt-header-sub {
    color: var(--dt-text-muted);
    font-size: 0.78rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin-top: 0.4rem;
    font-weight: 500;
}

/* -------------------------------- Sidebar ------------------------------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a101c 0%, #0b1322 100%);
    border-right: 1px solid var(--dt-border);
}
section[data-testid="stSidebar"] * { color: var(--dt-text) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--dt-border); }

.dt-sb-brand {
    text-align: center;
    padding: 0.35rem 0 0.55rem 0;
    border-bottom: 1px solid var(--dt-border);
    margin-bottom: 0.9rem;
}
.dt-sb-logo {
    font-size: 1.9rem;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.dt-sb-title {
    font-size: 1.02rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    background: linear-gradient(92deg, #22d3ee, #818cf8);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.dt-sb-sub {
    font-size: 0.68rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--dt-text-muted);
    margin-top: 0.15rem;
}
.dt-sb-user {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(255, 255, 255, 0.03));
    border: 1px solid rgba(34, 211, 238, 0.25);
    border-radius: 14px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.dt-sb-user-label {
    font-size: 0.66rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--dt-text-muted);
}
.dt-sb-user-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--dt-text);
    margin-top: 0.15rem;
}

/* Sidebar navigation -> pill buttons */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 0.3rem;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 0.6rem 0.85rem;
    margin: 0;
    transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateX(2px);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.16), rgba(129, 140, 248, 0.10));
    border-color: rgba(34, 211, 238, 0.42);
    box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.14), 0 6px 18px rgba(0, 0, 0, 0.3);
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
    color: #a5f3fc !important;
    font-weight: 600;
}

/* ------------------------- Cards (glass panels) ------------------------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(160deg, var(--dt-card-strong), var(--dt-card));
    border: 1px solid var(--dt-border) !important;
    border-radius: 18px !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    padding: 0.3rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--dt-border-strong) !important;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
div[data-testid="stVerticalBlockBorderWrapper"] * { color: var(--dt-text); }

/* --------------------------- Typography --------------------------- */
h1, h2, h3, h4, h5, h6 {
    color: var(--dt-text) !important;
    letter-spacing: -0.015em;
}
.stMarkdown, .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--dt-text-muted) !important;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    color: var(--dt-text) !important;
}

/* ------------------------------ Metric cards ----------------------------- */
div[data-testid="stMetric"] {
    background: linear-gradient(140deg, rgba(34, 211, 238, 0.10), rgba(255, 255, 255, 0.03));
    border: 1px solid rgba(34, 211, 238, 0.24);
    border-radius: 14px;
    padding: 0.9rem 1rem;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
div[data-testid="stMetricValue"] { color: var(--dt-text) !important; font-weight: 700; }
div[data-testid="stMetricLabel"] { color: var(--dt-text-muted) !important; font-weight: 500; }
div[data-testid="stMetricDelta"] { color: var(--dt-success) !important; }

/* -------------------------------- Buttons ------------------------------- */
.stButton > button, .stFormSubmitButton > button {
    background: linear-gradient(135deg, #06b6d4 0%, #0284c7 100%);
    color: #ffffff !important;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    padding: 0.55rem 1.15rem;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.28);
    transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #22d3ee 0%, #0ea5e9 100%);
    color: #ffffff !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 28px rgba(34, 211, 238, 0.42);
    filter: brightness(1.05);
}
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(0); }
.stButton > button p, .stFormSubmitButton > button p { color: #ffffff !important; font-weight: 600; }
.stButton > button[kind="secondary"], .stFormSubmitButton > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid var(--dt-border);
    box-shadow: none;
}
.stButton > button[kind="secondary"] p { color: var(--dt-text) !important; }

/* ----------------------------- Progress bars ----------------------------- */
div[data-testid="stProgress"] > div {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    overflow: hidden;
}
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #22d3ee, #38bdf8);
    border-radius: 999px;
    box-shadow: 0 0 12px rgba(34, 211, 238, 0.5);
}
div[data-testid="stProgress"] label, div[data-testid="stProgress"] p {
    color: var(--dt-text-muted) !important;
}

/* ----------------------- Form inputs (dark surfaces) ---------------------- */
input, textarea, select,
.stSelectbox div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
    background-color: var(--dt-input-bg) !important;
    color: var(--dt-input-text) !important;
    border: 1px solid var(--dt-border) !important;
    border-radius: 10px !important;
}
input, textarea {
    color: var(--dt-input-text) !important;
    caret-color: var(--dt-accent) !important;
    -webkit-text-fill-color: var(--dt-input-text) !important;
}
input::placeholder, textarea::placeholder {
    color: var(--dt-placeholder) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--dt-placeholder) !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stDateInput label, .stTimeInput label,
.stSlider label, .stRadio label, .stCheckbox label {
    color: var(--dt-text) !important;
}
div[data-baseweb="select"] * { color: var(--dt-input-text) !important; }
div[data-baseweb="select"] svg { fill: var(--dt-text-muted) !important; }
div[data-baseweb="popover"] {
    background-color: #0d1626 !important;
    border: 1px solid var(--dt-border) !important;
    border-radius: 12px;
    color: var(--dt-input-text) !important;
}
div[data-baseweb="popover"] li { color: var(--dt-input-text) !important; }
div[data-baseweb="popover"] li:hover { background-color: rgba(34, 211, 238, 0.12) !important; }
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    background-color: rgba(255, 255, 255, 0.08) !important;
    color: var(--dt-input-text) !important;
}
div[data-baseweb="input"] input { color: var(--dt-input-text) !important; }
div[data-testid="stSlider"] label, div[data-testid="stSlider"] div { color: var(--dt-text) !important; }
div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {
    background: var(--dt-accent) !important;
    box-shadow: 0 0 0 4px rgba(34, 211, 238, 0.22);
}

/* --------------------------- DataFrames / editors -------------------------- */
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--dt-border);
    background-color: rgba(255, 255, 255, 0.02);
}
div[data-testid="stDataFrame"] [role="grid"], div[data-testid="stDataFrame"] * {
    color: var(--dt-text) !important;
}
div[data-testid="stDataEditor"] * { color: var(--dt-input-text) !important; }

/* ---------------------------------- Tabs ---------------------------------- */
button[data-baseweb="tab"] { color: var(--dt-text-muted) !important; }
button[data-baseweb="tab"] p { color: inherit !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--dt-accent) !important;
    border-bottom-color: var(--dt-accent) !important;
}
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--dt-accent) !important; }
div[data-baseweb="tab-highlight"] { background-color: var(--dt-accent) !important; }
div[data-baseweb="tab-border"] { background-color: var(--dt-border) !important; }

/* -------------------------------- Expanders ------------------------------- */
div[data-testid="stExpander"] details {
    background: var(--dt-card);
    border: 1px solid var(--dt-border);
    border-radius: 12px;
    transition: border-color 0.2s ease;
}
div[data-testid="stExpander"] details:hover { border-color: var(--dt-border-strong); }
div[data-testid="stExpander"] details summary { color: var(--dt-text) !important; font-weight: 500; }
div[data-testid="stExpander"] details summary:hover { color: var(--dt-accent) !important; }
div[data-testid="stExpander"] details p, div[data-testid="stExpander"] details label,
div[data-testid="stExpander"] details div { color: var(--dt-text) !important; }

/* ---------------------------- Checkboxes / radios -------------------------- */
.stCheckbox label span { color: var(--dt-text) !important; }
div[role="radiogroup"] label span { color: var(--dt-text) !important; }

/* ---------------------------- Footer (fixed band) --------------------------- */
.st-key-app_footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    z-index: 999;
    background: rgba(7, 10, 18, 0.82);
    backdrop-filter: blur(14px);
    border-top: 1px solid var(--dt-border);
    padding: 0.5rem 2rem 0.3rem 2rem;
}
.st-key-app_footer button {
    background: transparent !important;
    color: var(--dt-text-muted) !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
.st-key-app_footer button p { color: var(--dt-text-muted) !important; }
.st-key-app_footer button:hover, .st-key-app_footer button:hover p {
    color: var(--dt-accent) !important;
}
.dt-footer-copy {
    text-align: center;
    width: 100%;
    display: block;
    color: var(--dt-text-muted);
    font-size: 0.78rem;
    padding-bottom: 0.2rem;
    letter-spacing: 0.05em;
}
.block-container {
    padding-bottom: 6.5rem !important;
}

/* ------------------------------ Popover body ------------------------------ */
div[data-testid="stPopoverBody"] {
    background: linear-gradient(160deg, #0d1626, #0a101c) !important;
    border: 1px solid var(--dt-border);
    border-radius: 14px;
    padding: 0.4rem 0.2rem;
    min-width: 280px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);
}
div[data-testid="stPopoverBody"] * { color: var(--dt-text) !important; }
.dt-popover-title {
    font-size: 1.05rem;
    font-weight: 700;
    background: linear-gradient(90deg, #22d3ee, #818cf8);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 0.4rem;
}
.dt-popover-body p, .dt-popover-body li { color: var(--dt-text) !important; font-size: 0.9rem; }
.dt-popover-body li { margin-bottom: 0.3rem; }

/* ------------------------------ Trend helpers ------------------------------ */
.dt-trend-up { color: #34d399; font-weight: 700; }
.dt-trend-down { color: #fb7185; font-weight: 700; }
.dt-trend-flat { color: #93a4bd; font-weight: 700; }

/* ------------------------------- Alerts / toasts ---------------------------- */
div[data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--dt-border);
    border-radius: 12px;
}
div[data-testid="stAlertContentSuccess"] { color: var(--dt-success) !important; }
div[data-testid="stAlertContentError"] { color: var(--dt-danger) !important; }
div[data-testid="stAlertContentWarning"] { color: var(--dt-gold) !important; }
div[data-testid="stAlertContentInfo"] { color: var(--dt-accent) !important; }
div[data-testid="stToastContainer"] > div {
    background: #0d1626;
    border: 1px solid var(--dt-border-strong);
    border-radius: 12px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}
</style>
"""


def inject_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def trend_html(label: str, value_text: str, trend_pct: float) -> str:
    if trend_pct > 0.5:
        cls, arrow = "dt-trend-up", "▲"
    elif trend_pct < -0.5:
        cls, arrow = "dt-trend-down", "▼"
    else:
        cls, arrow = "dt-trend-flat", "→"
    return (
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.08);'>"
        f"<div><b style='color:#e8eef7;'>{label}</b><br>"
        f"<span style='color:#93a4bd;font-size:0.8rem;'>{value_text}</span></div>"
        f"<div class='{cls}'>{arrow} {abs(trend_pct):.1f}%</div></div>"
    )
