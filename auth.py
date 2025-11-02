import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
import copy

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
# auth.py (fixed init_authenticator)

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
def init_authenticator():
    # 🔥 THE NEW FIX: Convert the Streamlit secrets proxy object to a standard dict 
    # before deepcopying, which breaks the infinite recursion loop in __getattr__.
    secrets_credentials_dict = dict(st.secrets["credentials"])
    credentials = copy.deepcopy(secrets_credentials_dict)
    
    # Cookie access is fine as it's a simple dictionary access
    cookie = st.secrets["cookie"]
    
    authenticator = stauth.Authenticate(
        credentials,
        cookie["name"],
        cookie["key"],
        cookie["expiry_days"]
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
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

# ─────────────────────────────────────────────
# Role detection
# ─────────────────────────────────────────────
def get_user_role(username):
    # NOTE: The credentials in secrets.toml use 'admin', 'colin', 'halley' as keys.
    # The library converts these to lowercase internally, so comparing against the 
    # username returned by the authenticator (which is the lowercase key) is correct.
    return "viewer" if username in ["colin", "halley"] else "admin"

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
