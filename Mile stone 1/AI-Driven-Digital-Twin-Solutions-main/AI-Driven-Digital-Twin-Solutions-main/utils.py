"""
utils.py
Simple, clean LIGHT theme (white / soft gray / teal accent), password
hashing, JWT auth tokens, and session-state helpers.
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


def get_cookie_token() -> str | None:
    """Retrieve dt_jwt token directly from HTTP request cookies in Streamlit context."""
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            tok = st.context.cookies.get("dt_jwt")
            if tok and isinstance(tok, str):
                return tok
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            cookie_str = st.context.headers.get("cookie") or st.context.headers.get("Cookie") or ""
            for part in cookie_str.split(";"):
                part = part.strip()
                if part.startswith("dt_jwt="):
                    return part.split("=", 1)[1]
    except Exception:
        pass
    return None


def restore_session() -> bool:
    """Re-hydrate the logged-in session from HTTP cookie, query param, or session_state."""
    if st.session_state.get("_clear_cookie"):
        return False

    token = get_cookie_token()
    if not token:
        token = st.query_params.get("auth")
        if isinstance(token, list):
            token = token[0] if token else None
    if not token:
        token = st.session_state.get("jwt_token")

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
    """Keep browser cookie & localStorage in sync with the current auth state."""
    if st.session_state.pop("_clear_cookie", False):
        components.html(
            "<script>"
            "document.cookie = 'dt_jwt=; path=/; max-age=0; SameSite=Lax';"
            "try { window.parent.document.cookie = 'dt_jwt=; path=/; max-age=0; SameSite=Lax'; } catch(e){}"
            "try { window.parent.localStorage.removeItem('dt_jwt'); } catch(e){}"
            "</script>",
            height=0,
        )
        return

    token = st.session_state.get("jwt_token")
    if token:
        components.html(
            "<script>"
            f"document.cookie = 'dt_jwt={token}; path=/; max-age={_JWT_EXPIRES_HOURS * 3600}; SameSite=Lax';"
            f"try {{ window.parent.document.cookie = 'dt_jwt={token}; path=/; max-age={_JWT_EXPIRES_HOURS * 3600}; SameSite=Lax'; }} catch(e){{}}"
            f"try {{ window.parent.localStorage.setItem('dt_jwt', '{token}'); }} catch(e){{}}"
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
# Theme CSS - LIGHT theme: white / soft-gray background, dark slate text,
# teal accent. Every selector below forces both a background AND a text
# color together so nothing can end up "light text on light background"
# or "dark text on dark background".
# --------------------------------------------------------------------------- #
THEME_CSS = """
<style>
:root {
    --dt-bg: #f4f6f9;
    --dt-bg-2: #ffffff;
    --dt-card: #ffffff;
    --dt-border: #d7dee6;
    --dt-accent: #0e7490;
    --dt-accent-2: #0891b2;
    --dt-text: #1e293b;
    --dt-text-muted: #52606d;
    --dt-input-bg: #ffffff;
    --dt-input-text: #0f172a;
    --dt-placeholder: #6b7280;
}

/* Base app background + default text color */
.stApp {
    background-color: var(--dt-bg);
    color: var(--dt-text);
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    color: var(--dt-text);
}

/* Native Streamlit top toolbar -> blends into the light theme */
header[data-testid="stHeader"] {
    background-color: var(--dt-bg) !important;
    box-shadow: none !important;
    border-bottom: 1px solid var(--dt-border);
}
header[data-testid="stHeader"] * {
    color: var(--dt-text) !important;
}
div[data-testid="stDecoration"] { display: none; }

/* Header */
.dt-header-wrap {
    text-align: center;
    padding: 0.6rem 0 1.2rem 0;
}
.dt-header-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--dt-accent);
    letter-spacing: 0.3px;
}
.dt-header-sub {
    color: var(--dt-text-muted);
    font-size: 0.85rem;
    margin-top: 0.15rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--dt-bg-2);
    border-right: 1px solid var(--dt-border);
}
section[data-testid="stSidebar"] * {
    color: var(--dt-text) !important;
}

/* Cards: any bordered container gets a simple flat white card style */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--dt-card);
    border: 1px solid var(--dt-border) !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}
div[data-testid="stVerticalBlockBorderWrapper"] * {
    color: var(--dt-text);
}

/* Headings / markdown text stay dark and readable everywhere */
h1, h2, h3, h4, h5, h6 { color: var(--dt-text) !important; }
.stMarkdown, .stMarkdown p, .stCaption, [data-testid="stCaptionContainer"] {
    color: var(--dt-text-muted) !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: #eef7fa;
    border: 1px solid #cfe9f0;
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
}
div[data-testid="stMetricValue"] { color: var(--dt-accent) !important; }
div[data-testid="stMetricLabel"] { color: var(--dt-text-muted) !important; }

/* Buttons */
.stButton > button, .stFormSubmitButton > button {
    background-color: var(--dt-accent-2);
    color: #ffffff !important;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.1rem;
    transition: background-color 0.15s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: var(--dt-accent);
    color: #ffffff !important;
}
.stButton > button p, .stFormSubmitButton > button p { color: #ffffff !important; }

/* Progress bars */
div[data-testid="stProgress"] > div > div {
    background-color: var(--dt-accent-2);
}
div[data-testid="stProgress"] > div {
    background-color: #dbe4ea;
}

/* --------------------------------------------------------------------- */
/* Form input & placeholder visibility (light theme: dark text on white) */
/* --------------------------------------------------------------------- */
input, textarea, select,
.stSelectbox div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
    background-color: var(--dt-input-bg) !important;
    color: var(--dt-input-text) !important;
    border: 1px solid var(--dt-border) !important;
    border-radius: 8px !important;
}
input, textarea {
    color: var(--dt-input-text) !important;
    caret-color: var(--dt-input-text) !important;
    -webkit-text-fill-color: var(--dt-input-text) !important;
}
input::placeholder, textarea::placeholder {
    color: var(--dt-placeholder) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--dt-placeholder) !important;
}
/* Labels above inputs (Email, Password, etc.) */
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stDateInput label, .stTimeInput label,
.stSlider label, .stRadio label, .stCheckbox label {
    color: var(--dt-text) !important;
}
/* Selectbox / multiselect selected-value text and dropdown options */
div[data-baseweb="select"] * { color: var(--dt-input-text) !important; }
div[data-baseweb="select"] svg { fill: var(--dt-text-muted) !important; }
div[data-baseweb="popover"] { background-color: #ffffff !important; }
div[data-baseweb="popover"] li { color: var(--dt-input-text) !important; }
div[data-baseweb="popover"] li:hover { background-color: #eef7fa !important; }
/* Number input +/- buttons */
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    background-color: #eef2f6 !important;
    color: var(--dt-input-text) !important;
}
/* Date / time inputs */
div[data-baseweb="input"] input { color: var(--dt-input-text) !important; }
/* Slider value + ticks */
div[data-testid="stSlider"] label, div[data-testid="stSlider"] div { color: var(--dt-text) !important; }

/* DataFrames / data editor */
div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--dt-border);
    background-color: #ffffff;
}

/* Tabs */
button[data-baseweb="tab"] { color: var(--dt-text-muted) !important; }
button[data-baseweb="tab"] p { color: inherit !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--dt-accent) !important;
    border-bottom-color: var(--dt-accent) !important;
}
button[data-baseweb="tab"][aria-selected="true"] p { color: var(--dt-accent) !important; }
div[data-baseweb="tab-highlight"] { background-color: var(--dt-accent) !important; }

/* --------------------------------------------------------------------- */
/* Footer band - fixed to the bottom, edge to edge, centered copyright   */
/* --------------------------------------------------------------------- */
.st-key-app_footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    z-index: 999;
    background-color: #ffffff;
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
    color: #64748b;
    font-size: 0.8rem;
    padding-bottom: 0.2rem;
}
.block-container {
    padding-bottom: 6rem !important;
}

/* Popover content - white card, dark readable text */
div[data-testid="stPopoverBody"] {
    background: #ffffff !important;
    border: 1px solid var(--dt-border);
    border-radius: 12px;
    padding: 0.4rem 0.2rem;
    min-width: 260px;
}
div[data-testid="stPopoverBody"] * { color: var(--dt-text) !important; }
.dt-popover-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--dt-accent) !important;
    margin-bottom: 0.4rem;
}
.dt-popover-body p, .dt-popover-body li { color: var(--dt-text) !important; font-size: 0.9rem; }
.dt-popover-body li { margin-bottom: 0.3rem; }

/* Trend pill helper classes (used via st.markdown) */
.dt-trend-up { color: #0f9d58; font-weight: 700; }
.dt-trend-down { color: #d93025; font-weight: 700; }
.dt-trend-flat { color: #52606d; font-weight: 700; }

/* Alerts (success / error / info / warning) - keep readable on light bg */
div[data-testid="stAlertContentSuccess"], div[data-testid="stAlertContentError"],
div[data-testid="stAlertContentInfo"], div[data-testid="stAlertContentWarning"] {
    color: var(--dt-text) !important;
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
        f"padding:0.4rem 0;border-bottom:1px solid #e2e8f0;'>"
        f"<div><b style='color:#1e293b;'>{label}</b><br>"
        f"<span style='color:#52606d;font-size:0.8rem;'>{value_text}</span></div>"
        f"<div class='{cls}'>{arrow} {abs(trend_pct):.1f}%</div></div>"
    )