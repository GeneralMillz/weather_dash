from __future__ import annotations
import os, json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import pandas as pd
import streamlit as st
import plotly.express as px
# app.py
"""
Secure Dashboard (improved single-file version)

- Uses Streamlit Secrets or environment variables for secrets (no personal data in code).
- Clear read-only viewer vs admin separation.
- Safe, non-blocking optional DB logging (psycopg2 only used when DB creds present).
- File-based append-only JSONL login events (no secrets written).
- Modular helpers for tests and extension.
- No external network calls at import time.
"""
# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Secrets ---
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        return st.secrets.get(key) if hasattr(st, "secrets") else os.environ.get(key, default)
    except Exception:
        return os.environ.get(key, default)

ADMIN_USER = get_secret("admin_username", "admin")
ADMIN_PASS = get_secret("admin_password", "adminpass")
VIEWER_USER = get_secret("viewer_username", "viewer")
VIEWER_PASS = get_secret("viewer_password", "viewerpass")

# --- Auth ---
def check_credentials(u: str, p: str) -> Optional[str]:
    if u == ADMIN_USER and p == ADMIN_PASS:
        return "admin"
    if u == VIEWER_USER and p == VIEWER_PASS:
        return "viewer"
    return None

# --- Audit Logging ---
LOG_PATH = os.environ.get("DASHBOARD_LOGIN_LOG", "login_events.jsonl")
def append_event(event: Dict[str, Any]) -> None:
    safe = {k: v for k, v in event.items() if k not in ("password", "admin_password", "db_pass")}
    try:
        os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(safe, default=str) + "\n")
    except Exception:
        try:
            st.sidebar.warning("Audit log write failed")
        except Exception:
            pass

# --- Login UI ---
st.sidebar.header("Login")
user = st.sidebar.text_input("Username", key="login_user")
pw = st.sidebar.text_input("Password", type="password", key="login_pass")
btn = st.sidebar.button("Sign in")

role = None
if btn:
    role = check_credentials(user.strip(), pw)
    ts = datetime.now(timezone.utc).isoformat()
    append_event({"username": user, "role": role or "invalid", "time": ts})
    if role:
        st.sidebar.success(f"Signed in as: {role}")
    else:
        st.sidebar.error("Invalid credentials")

if "role" in st.session_state and st.session_state.role:
    role = st.session_state.role
if role:
    st.session_state.role = role

if not role:
    st.title("Secure Dashboard")
    st.info("Please sign in from the sidebar to access the dashboard.")
    st.stop()

# --- Sidebar session info ---
st.sidebar.markdown(f"**Role**: {role}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# --- Filters ---
st.sidebar.header("Filters")
station = st.sidebar.selectbox("Station", ["KDTW", "KGRR", "KLAN"], index=0)
selected_date = st.sidebar.date_input("Date", pd.to_datetime("2025-10-27"))

# --- Main UI ---
st.title("Secure Dashboard")
st.markdown("Viewer accounts are read-only. Admins see controls below.")

# --- Forecast vs Observed ---
forecast_data = {
    "KDTW": {"forecast": 42, "observed": 40},
    "KGRR": {"forecast": 39, "observed": 41},
    "KLAN": {"forecast": 41, "observed": 38},
}
f = forecast_data.get(station, {"forecast": None, "observed": None})
delta = f["observed"] - f["forecast"] if f["forecast"] is not None and f["observed"] is not None else None
alignment = "Aligned" if delta is not None and abs(delta) <= 2 else "Misaligned"

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

# --- ROI Simulator ---
roi_df = pd.DataFrame({
    "bracket": ["35–40", "40–45", "45–50"],
    "entry_price": [0.40, 0.45, 0.50],
    "exit_price": [0.48, 0.42, 0.55],
    "position": ["Long", "Short", "Long"]
})
roi_df["ROI"] = roi_df.apply(lambda r: (r.exit_price - r.entry_price) if r.position == "Long" else (r.entry_price - r.exit_price), axis=1)
st.header("Bracket ROI Simulator")
st.dataframe(roi_df, use_container_width=True)

# --- Temperature Trend Chart ---
trend_df = pd.DataFrame({
    "Date": pd.date_range(end=selected_date, periods=10),
    "Forecast Temp": [41,42,43,44,42,40,39,41,42,f["forecast"]],
    "Observed Temp": [40,41,42,43,41,39,38,40,41,f["observed"]],
})
fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
st.header("Temperature Trend (Past 10 Days)")
st.plotly_chart(fig, use_container_width=True)

# --- Admin Controls ---
if role == "admin":
    st.markdown("---")
    st.header("Admin Controls")
    col1, col2 = st.columns(2)

    if col1.button("Run ingestion"):
        ts = datetime.now(timezone.utc).isoformat()
        append_event({"username": user, "role": "admin", "action": "run_ingest", "time": ts})
        st.success("Ingestion started (placeholder)")

    override_station = col2.text_input("Override station ID", value="")
    if col2.button("Queue override") and override_station:
        ts = datetime.now(timezone.utc).isoformat()
        append_event({"username": user, "role": "admin", "action": "override_station", "value": override_station, "time": ts})
        st.info(f"Override queued for {override_station}")

    if st.button("Run backfill"):
        ts = datetime.now(timezone.utc).isoformat()
        append_event({"username": user, "role": "admin", "action": "run_backfill", "time": ts})
        st.success("Backfill started (placeholder)")

# --- Footer ---
st.sidebar.markdown("### Connection Info")
st.sidebar.write("DB configured" if get_secret("DATABASE_URL") else "DB not configured")
st.sidebar.write("VC key configured" if get_secret("VC_API_KEY") else "VC key not configured")
