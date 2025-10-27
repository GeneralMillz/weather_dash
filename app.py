import streamlit as st
import streamlit_authenticator as stauth

# --- Authentication setup ---
# In production, store hashed passwords. For tonight, you can start with plain text.
credentials = {
    "usernames": {
        "jerry": {
            "email": st.secrets.get("app_admin_email", "you@example.com"),
            "name": "Jerry",
            "password": st.secrets.get("app_password", "changeme")  # replace in secrets
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "kalshi_dashboard_cookie",   # cookie name
    "kalshi_dashboard_signature",# key for signing
    cookie_expiry_days=7
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    # --- Your dashboard content goes here ---
    st.title("Ops Dashboard")
    st.write("Baseline deploy works. Replace this with your schema tiles, charts, etc.")

elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.info("Please log in")
