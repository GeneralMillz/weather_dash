import streamlit as st
import streamlit_authenticator as stauth
from datetime import datetime

def load_credentials_from_secrets():
    admin_username = st.secrets["admin_username"]
    admin_email = st.secrets["admin_email"]
    admin_password = st.secrets["admin_password"]
    viewer_username = st.secrets["viewer_username"]
    viewer_email = st.secrets["viewer_email"]
    viewer_password = st.secrets["viewer_password"]

    credentials = {
        "usernames": {
            admin_username: {"email": admin_email, "name": "Admin", "password": admin_password},
            viewer_username: {"email": viewer_email, "name": "Viewer", "password": viewer_password},
        }
    }
    return credentials, admin_username, viewer_username

def init_authenticator():
    credentials, admin_username, viewer_username = load_credentials_from_secrets()
    authenticator = stauth.Authenticate(
        credentials,
        "weatherdash_cookie",
        "weatherdash_signature",
        cookie_expiry_days=7
    )
    return authenticator, admin_username, viewer_username

def login_ui(authenticator):
    # For streamlit-authenticator v0.4.2 use positional args: form_name, location
    name, auth_status, username = authenticator.login("Login", "sidebar")
    return name, auth_status, username

def logout_ui(authenticator, name):
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

def is_viewer(username, viewer_username):
    return username == viewer_username

def session_info(username, name):
    login_time = datetime.utcnow().isoformat()
    st.sidebar.markdown(f"**User**: {username}")
    st.sidebar.markdown(f"**Login (UTC)**: {login_time}")
    return login_time
