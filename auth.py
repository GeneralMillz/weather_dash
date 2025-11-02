import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime
import copy
import json 

# ─────────────────────────────────────────────
# Initialize authenticator
# ─────────────────────────────────────────────
def init_authenticator():
    # 🔥 THE DEFINITIVE FIX: Manually convert all nested AttrDicts to pure Python dicts.
    # This completely bypasses the RecursionError and the JSON serialization error.
    
    # 1. Initialize a pure Python dictionary structure to hold the converted credentials
    pure_credentials = {
        'usernames': {},
    }
    
    # Safely get the credentials section from secrets
    secrets_creds = st.secrets.get("credentials", {})
    
    # 2. Manually convert the nested 'usernames' AttrDict into a pure dict
    usernames_proxy = secrets_creds.get('usernames', {})
    
    for username, user_data_proxy in usernames_proxy.items():
        # Convert the inner user_data AttrDict (email, name, password) 
        # to a standard Python dictionary using dict().
        pure_credentials['usernames'][username] = dict(user_data_proxy) 
        
    # 3. Convert the 'cookie' AttrDict (needed for separate arguments later)
    cookie = dict(st.secrets.get('cookie', {}))
    
    # 4. Add the cookie and preauthorized data back to the main credentials dict
    pure_credentials['cookie'] = cookie
    pure_credentials['preauthorized'] = dict(st.secrets.get('preauthorized', {}))
    
    # Use the now-safe dictionary for authentication
    authenticator = stauth.Authenticate(
        pure_credentials, 
        cookie["name"],
        cookie["key"],
        cookie["expiry_days"]
    )
    return authenticator

# ─────────────────────────────────────────────
# Login UI
# ─────────────────────────────────────────────
def login_ui(authenticator):
    # FIX: Removed 'form_name' keyword argument, which caused a TypeError.
    name, auth_status, username = authenticator.login(
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
