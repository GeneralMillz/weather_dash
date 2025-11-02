import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime

# ─────────────────────────────────────────────
# Load credentials from secrets
# ─────────────────────────────────────────────
def load_credentials_from_secrets():
    usernames = {}
    users = st.secrets.get("users", {})

    for uname, udata in users.items():
        usernames[uname] = {
            "email": udata["email"],
            "name": uname.capitalize(),
            "password": udata["password"]
        }

    credentials = {"usernames": usernames}
    return credentials

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
def init_authenticator():
    credentials = load_credentials_from_secrets()
    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name="weatherdash_cookie",
        key="weatherdash_signature",
        cookie_expiry_days=7
    )
    return authenticator

# ─────────────────────────────────────────────
# Login UI
# ─────────────────────────────────────────────
def login_ui(authenticator):
    name, auth_status, username = authenticator.login(
        form_name="Login",
        location="sidebar"
    )
    return name, auth_status, username

# ─────────────────────────────────────────────
# Logout UI
# ─────────────────────────────────────────────
def logout_ui(authenticator, name):
    authenticator.logout(button_name="Logout", location="sidebar")
    st.sidebar.success(f"Logged in as {name}")

# ─────────────────────────────────────────────
# Role detection
# ─────────────────────────────────────────────
def get_user_role(username):
    return st.secrets["users"].get(username, {}).get("role", "viewer")

def is_viewer(username):
    return get_user_role(username) == "viewer"

def is_admin(username):
    return get_user_role(username) == "admin"

# ─────────────────────────────────────────────
# Session info display
# ─────────────────────────────────────────────
def session_info(username, name):
    login_time = datetime.utcnow().isoformat()
    st.sidebar.markdown(f"👤 **{name}** ({username})")
    st.sidebar.caption(f"🔒 Session started: {login_time[:16]} UTC")
    return login_time
