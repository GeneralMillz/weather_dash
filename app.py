from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import json, os
from datetime import datetime, timezone
from tile_manifest import TILES, TAB_LABELS

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# ─────────────────────────────────────────────
# Load credentials from secrets
# ─────────────────────────────────────────────
admin_username = st.secrets["admin_username"]
admin_email = st.secrets["admin_email"]
admin_password = st.secrets["admin_password"]

viewer_username = st.secrets["viewer_username"]
viewer_email = st.secrets["viewer_email"]
viewer_password = st.secrets["viewer_password"]

# ─────────────────────────────────────────────
# Build credentials dictionary
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Authenticator setup
# ─────────────────────────────────────────────
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",
    "dashboard_signature",
    cookie_expiry_days=7
)

# ─────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────
name, auth_status, user_key = authenticator.login()

def is_viewer(u_key):
    return u_key == viewer_username

def append_login_event(event: dict):
    try:
        log_dir = os.getenv("LOG_DIR", "./logs")
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, "login_events.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        st.sidebar.warning("Login logging failed.")

# ─────────────────────────────────────────────
# Authenticated session
# ─────────────────────────────────────────────
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

    # ─────────────────────────────────────────────
    # Filters
    # ─────────────────────────────────────────────
    st.sidebar.header("Filters")
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"])
    selected_date = st.sidebar.date_input("Select Date", pd.to_datetime("2025-10-27"))

    # ─────────────────────────────────────────────
    # Dashboard layout
    # ─────────────────────────────────────────────
    st.title("Secure Dashboard")
    st.markdown("Viewer accounts are read-only. Admins see controls below.")

    selected_tab = st.sidebar.radio("Dashboard Sections", list(TILES.keys()), format_func=lambda k: TAB_LABELS.get(k, k))
    st.markdown(f"## {TAB_LABELS.get(selected_tab, selected_tab)}")

    for tile_name in TILES[selected_tab]:
        try:
            mod = __import__(f"tiles.{tile_name}", fromlist=["render"])
            mod.render(None, st, {"user": user_key, "now_iso": lambda: login_time})
        except Exception as e:
            st.error(f"❌ Tile `{tile_name}` failed: {e}")

else:
    if auth_status is False:
        st.error("Invalid credentials")
    else:
        st.info("Please log in to access the dashboard.")
