from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import json, os
from datetime import datetime, timezone

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Load credentials from secrets ---
admin_username = st.secrets["admin_username"]
admin_email = st.secrets["admin_email"]
admin_password = st.secrets["admin_password"]

viewer_username = st.secrets["viewer_username"]
viewer_email = st.secrets["viewer_email"]
viewer_password = st.secrets["viewer_password"]

db_user = st.secrets.get("db_user", "")
db_pass = st.secrets.get("db_pass", "")

# --- Build credentials dictionary ---
credentials = {
    "usernames": {
        admin_username: {
            "email": admin_email,
            "name": "Admin",
            "password": admin_password
        },
        viewer_username: {
            "email": viewer_email,
            "name": "Viewer",
            "password": viewer_password
        }
    }
}

# --- Authenticator setup ---
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",
    "dashboard_signature",
    cookie_expiry_days=7
)

# --- Login ---
name, auth_status, user_key = authenticator.login("Login", "main")

# --- Helper ---
def is_viewer(u_key):
    return u_key == viewer_username

# --- Logging ---
def append_login_event(event: dict):
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/login_events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        st.sidebar.warning("Login logging failed.")

# --- Authenticated session ---
if auth_status:
    login_time = datetime.now(timezone.utc).isoformat()
    st.sidebar.markdown(f"**User**: {user_key}")
    st.sidebar.markdown(f"**Login (UTC)**: {login_time}")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    # Log login event
    event = {
        "username": user_key,
        "display_name": name,
        "login_time": login_time,
        "is_viewer": is_viewer(user_key)
    }
    append_login_event(event)

    # --- Filters ---
    st.sidebar.header("Filters")
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"])
    selected_date = st.sidebar.date_input("Select Date", pd.to_datetime("2025-10-27"))

    # --- Dashboard ---
    st.title("Secure Dashboard")
    st.markdown("Viewer accounts are read-only. Admins see controls below.")

    # Forecast vs Observed
    forecast_data = {
        "KDTW": {"forecast": 42, "observed": 40},
        "KGRR": {"forecast": 39, "observed": 41},
        "KLAN": {"forecast": 41, "observed": 38}
    }
    f = forecast_data.get(station, {"forecast": None, "observed": None})
    delta = f["observed"] - f["forecast"]
    alignment = "Aligned" if abs(delta) <= 2 else "Misaligned"
    comp_df = pd.DataFrame([{
        "Station": station,
        "Date": selected_date.strftime("%Y-%m-%d"),
        "Forecast Temp": f["forecast"],
        "Observed Temp": f["observed"],
        "Delta": delta,
        "Alignment": alignment
    }])
    st.header("Forecast vs Observed Comparison")
    st.dataframe(comp_df, use_container_width=True)

    # ROI Simulator
    st.header("Bracket ROI Simulator")
    roi_df = pd.DataFrame({
        "bracket": ["35–40", "40–45", "45–50"],
        "entry_price": [0.40, 0.45, 0.50],
        "exit_price": [0.48, 0.42, 0.55],
        "position": ["Long", "Short", "Long"]
    })
    roi_df["ROI"] = roi_df.apply(lambda r: (r.exit_price - r.entry_price) if r.position == "Long" else (r.entry_price - r.exit_price), axis=1)
    st.dataframe(roi_df, use_container_width=True)

    # Trend Chart
    st.header("Temperature Trend (Past 10 Days)")
    trend_df = pd.DataFrame({
        "Date": pd.date_range(end=selected_date, periods=10),
        "Forecast Temp": [41,42,43,44,42,40,39,41,42,f["forecast"]],
        "Observed Temp": [40,41,42,43,41,39,38,40,41,f["observed"]],
    })
    fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
    st.plotly_chart(fig, use_container_width=True)

    # Admin Controls
    if not is_viewer(user_key):
        st.header("Admin Controls")
        if st.button("Run ingestion"):
            st.success("Ingestion started (placeholder)")
        override_station = st.text_input("Override station ID", value="")
        if st.button("Queue override") and override_station:
            st.info(f"Override queued for {override_station}")
        if st.button("Run backfill"):
            st.success("Backfill started (placeholder)")

else:
    if auth_status is False:
        st.error("Invalid credentials")
    else:
        st.info("Please log in to access the dashboard.")
