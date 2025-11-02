import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
import copy

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
def init_authenticator():
    # FIX: Use deepcopy to get a completely independent, writable copy 
    # of the credentials dictionary from the read-only st.secrets object.
    credentials = copy.deepcopy(st.secrets["credentials"])
    
    # The 'cookie' dictionary can be used directly as it is not modified by the library, 
    # but accessing it via st.secrets is safer than a shallow copy if it contained nested objects.
    # However, since it is a simple dict, direct access is fine.
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
