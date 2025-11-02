import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
import copy
import json # REQUIRED for the definitive fix

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
def init_authenticator():
    # 🔥 THE DEFINITIVE FIX FOR RECURSIONERROR 🔥
    # Streamlit's st.secrets returns proxy objects. Deepcopying them 
    # causes infinite recursion. We use JSON serialization/deserialization
    # to convert the credentials to a pure, recursion-safe Python dict.
    
    # 1. Get the credentials proxy object and convert the top level to a basic dict
    credentials_proxy = dict(st.secrets["credentials"])

    # 2. Serialize to JSON string and deserialize back to a pure Python dict.
    # This process converts all nested proxy dicts into standard dicts,
    # breaking the recursive link.
    try:
        credentials_json = json.dumps(credentials_proxy)
        credentials = json.loads(credentials_json) 
    except Exception as e:
        # If this step fails, something is seriously wrong with secrets structure
        st.error(f"FATAL: Failed to convert secrets to pure dictionary: {e}")
        return None 
    
    # Cookie access is fine as it's a simple dictionary access
    cookie = st.secrets["cookie"]
    
    authenticator = stauth.Authenticate(
        credentials, # Pass the pure, recursion-safe dictionary
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
    # Assign 'viewer' role to specific users, otherwise 'admin'.
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
