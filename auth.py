import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime

def init_authenticator():
    settings = st.secrets["settings"]
    authenticator = stauth.Authenticate(
        credentials=st.secrets["credentials"],
        cookie_name=settings["cookie"]["name"],
        key=settings["cookie"]["key"],
        cookie_expiry_days=settings["cookie"]["expiry_days"]
    )
    return authenticator

def login_ui(authenticator):
    name, auth_status, username = authenticator.login(
        form_name="Login",
        location="sidebar"
    )
    return name, auth_status, username

def logout_ui(authenticator, name):
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

def get_user_role(username):
    return "viewer" if username in ["colin", "halley"] else "admin"

def is_viewer(username):
    return get_user_role(username) == "viewer"

def is_admin(username):
    return get_user_role(username) == "admin"

def session_info(username, name):
    login_time = datetime.utcnow().isoformat()
    st.sidebar.markdown(f"👤 **{name}** ({username})")
    st.sidebar.caption(f"🔒 Session started: {login_time[:16]} UTC")
    return login_time
