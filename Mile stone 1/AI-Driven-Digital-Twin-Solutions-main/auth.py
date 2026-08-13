"""
auth.py
Login, registration, and forgot-password screens shown before a user
reaches the main app.
"""

import streamlit as st

import database as db
from utils import create_token, flash, hash_password, validate_token, verify_password


def _start_session(user: dict) -> None:
    """Persist identity in session state and mint a signed JWT for the user."""
    st.session_state.logged_in = True
    st.session_state.user_id = user["user_id"]
    st.session_state.user_name = user["name"]
    st.session_state.user_gender = user["gender"]
    st.session_state.page = "Dashboard"
    token = create_token(
        {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "gender": user["gender"],
        }
    )
    st.session_state.jwt_token = token
    st.session_state.jwt_exp = validate_token(token)["exp"]
    try:
        if "auth" in st.query_params:
            st.query_params.pop("auth")
    except Exception:
        pass


def render_auth():
    # Fix 3: dedicated Forgot Password view, toggled via session_state.auth_mode
    if st.session_state.get("auth_mode") == "ForgotPassword":
        _render_forgot_password()
        return

    st.markdown(
        "<div style='text-align:center;margin-top:1rem;margin-bottom:1.5rem;"
        "color:#52606d;'>Sign in to load your digital twin, or create a new one.</div>",
        unsafe_allow_html=True,
    )

    left, mid, right = st.columns([1, 1.4, 1])
    with mid:
        with st.container(border=True):
            tabs = st.tabs(["Login", "Register"])

            # ---------------- Login ----------------
            with tabs[0]:
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", placeholder="Your password")
                    submitted = st.form_submit_button("Sign In", width='stretch')
                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        user = db.get_user_by_email(email.strip().lower())
                        if user and verify_password(password, user["password_hash"]):
                            _start_session(user)
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

                if st.button("Forgot Password?", key="forgot_pw_link", width='stretch'):
                    st.session_state.auth_mode = "ForgotPassword"
                    st.rerun()

            # ---------------- Register ----------------
            with tabs[1]:
                with st.form("register_form"):
                    name = st.text_input("Full Name", placeholder="Jane Doe")
                    email_r = st.text_input("Email ", key="reg_email", placeholder="you@example.com")
                    gender = st.selectbox("Gender", ["Male", "Female"])
                    age = st.number_input("Age", min_value=10, max_value=100, value=25)
                    occupation = st.text_input("Occupation", placeholder="e.g. Software Engineer")
                    password_r = st.text_input("Password ", type="password", key="reg_pw", placeholder="Create a password")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                    submitted_r = st.form_submit_button("Create My Digital Twin", width='stretch')
                if submitted_r:
                    if not (name and email_r and password_r):
                        st.error("Name, email, and password are required.")
                    elif password_r != confirm:
                        st.error("Passwords do not match.")
                    elif db.get_user_by_email(email_r.strip().lower()):
                        st.error("An account with this email already exists.")
                    else:
                        uid = db.create_user(
                            name.strip(),
                            email_r.strip().lower(),
                            hash_password(password_r),
                            gender,
                            int(age),
                            occupation.strip(),
                        )
                        _start_session(
                            {
                                "user_id": uid,
                                "name": name.strip(),
                                "email": email_r.strip().lower(),
                                "gender": gender,
                            }
                        )
                        flash("Account created! Loading your dashboard...")
                        st.rerun()


def _render_forgot_password():
    """Fix 3: Forgot Password page - collects email, shows a generic success
    message (dummy reset logic), and offers a way back to the Login view."""
    st.markdown(
        "<div style='text-align:center;margin-top:1rem;margin-bottom:1.5rem;"
        "color:#52606d;'>Reset access to your digital twin.</div>",
        unsafe_allow_html=True,
    )

    left, mid, right = st.columns([1, 1.4, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### 🔑 Forgot Password")
            st.caption("Enter your registered email address and we'll send you a reset link.")

            with st.form("forgot_password_form"):
                reset_email = st.text_input("Registered Email", placeholder="you@example.com")
                reset_submitted = st.form_submit_button("Reset Password", width='stretch')

            if reset_submitted:
                if not reset_email or "@" not in reset_email:
                    st.error("Please enter a valid email address.")
                else:
                    # Dummy logic: always show the same generic message so we
                    # never reveal whether an email is actually registered.
                    st.success("✅ If this email is registered, a reset link has been sent.")

            st.write("")
            if st.button("⬅️ Back to Login", key="back_to_login", width='stretch'):
                st.session_state.auth_mode = "Login"
                st.rerun()