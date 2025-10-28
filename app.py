import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Load credentials from secrets ---
username = st.secrets["username"]
email = st.secrets["email"]
password = st.secrets["password"]

credentials = {
    "usernames": {
        username: {
            "email": email,
            "name": "Admin",
            "password": password
        }
    }
}

# --- Authenticator setup (plain text allowed) ---
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",
    "dashboard_signature",
    cookie_expiry_days=7,
    preauthorized=False
)

# --- Login ---
name, auth_status, username = authenticator.login()

# --- Authenticated session ---
if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    st.title("Secure Dashboard")
    st.write("✅ Deploy works. Replace this with your schema tiles, Kalshi ladder logic, or NOAA audit panels.")

    # Example chart
    df = pd.DataFrame({
        "timestamp": pd.date_range(start="2025-10-01", periods=10, freq="D"),
        "price": [0.42, 0.45, 0.47, 0.44, 0.49, 0.51, 0.53, 0.50, 0.48, 0.52]
    })
    fig = px.line(df, x="timestamp", y="price", title="Sample Market Price Over Time")
    st.plotly_chart(fig, use_container_width=True)

elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.info("Please log in to access the dashboard.")
