import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")
@@ -53,8 +56,76 @@
def is_viewer(u_key):
    return u_key == viewer_username

# --- Logging utilities ---
LOG_PATH = "login_events.log"

def append_login_event(event: dict):
    """
    Append a JSON line to LOG_PATH. Does not log secrets.
    """
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    except Exception:
        # directory creation may fail if dirname is empty; ignore
        pass

    event_line = json.dumps(event, default=str)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(event_line + "\n")
    except Exception as e:
        # If file logging fails, surface a non-sensitive warning in the sidebar
        st.sidebar.warning("Login logging file write failed.")

def try_db_log(event: dict):
    """
    Optional: attempt to write login event to a DB if psycopg2 is available and db_user/db_pass present.
    This is non-blocking and will fail silently on missing dependencies or connectivity.
    """
    if not db_user or not db_pass:
        return
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_pass,
            host="localhost",
            port=5432,
            connect_timeout=2
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_login_events (
                id SERIAL PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                login_time TIMESTAMP,
                station TEXT,
                selected_date DATE,
                is_viewer BOOLEAN
            )
        """)
        conn.commit()
        cur.execute(
            "INSERT INTO user_login_events (username, display_name, login_time, station, selected_date, is_viewer) VALUES (%s,%s,%s,%s,%s,%s)",
            (event.get("username"), event.get("display_name"), event.get("login_time"), event.get("station"), event.get("selected_date"), event.get("is_viewer"))
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        # intentionally silent to avoid breaking the app if DB logging isn't configured
        return

# --- Authenticated session ---
if auth_status:
    # Record basic login metadata (no secrets)
    login_time = datetime.utcnow().isoformat()
    # Minimal sidebar info for the current session; user sees timestamp but not secrets
    st.sidebar.markdown(f"**User**: {user_key}")
    st.sidebar.markdown(f"**Login (UTC)**: {login_time}")

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

@@ -66,6 +137,20 @@ def is_viewer(u_key):
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"])
    selected_date = st.sidebar.date_input("Select Date", pd.to_datetime("2025-10-27"))

    # Log the login event (and current filters) to file and optionally DB
    event = {
        "username": user_key,
        "display_name": name,
        "login_time": login_time,
        "station": station,
        "selected_date": selected_date.strftime("%Y-%m-%d"),
        "is_viewer": is_viewer(user_key)
    }
    # Append to local log
    append_login_event(event)
    # Attempt DB log non-blocking
    try_db_log(event)

    # --- Forecast vs Observed Comparison (read-only) ---
    st.header("Forecast vs Observed Comparison")

@@ -98,7 +183,6 @@ def is_viewer(u_key):

    # --- Bracket ROI Simulator (read-only) ---
    st.header("Bracket ROI Simulator")

    roi_df = pd.DataFrame({
        "bracket": ["35–40", "40–45", "45–50"],
        "entry_price": [0.40, 0.45, 0.50],
@@ -113,7 +197,6 @@ def is_viewer(u_key):

    # --- Kalshi Weather Market Snapshot (read-only) ---
    st.header("Kalshi Weather Market Snapshot")
    # Placeholder snapshot; replace with live API when available
    kalshi_df = pd.DataFrame({
        "Market": [
            "Will it snow in Detroit?",
@@ -145,19 +228,54 @@ def is_viewer(u_key):
            run_ingest = st.button("Run ingestion")
            if run_ingest:
                st.success("Ingestion started (placeholder).")
                # Admin action should be logged as well
                admin_event = {
                    "username": user_key,
                    "display_name": name,
                    "action": "run_ingest",
                    "time": datetime.utcnow().isoformat()
                }
                append_login_event(admin_event)
                try_db_log(admin_event)

            override_station = st.text_input("Override station ID", value="")
            if override_station:
                st.write(f"Override queued for station: {override_station}")
                admin_event = {
                    "username": user_key,
                    "display_name": name,
                    "action": "override_station",
                    "override_value": override_station,
                    "time": datetime.utcnow().isoformat()
                }
                append_login_event(admin_event)
                try_db_log(admin_event)

        with st.expander("Manual Actions"):
            run_backfill = st.button("Run backfill")
            if run_backfill:
                st.success("Backfill started (placeholder).")
                admin_event = {
                    "username": user_key,
                    "display_name": name,
                    "action": "run_backfill",
                    "time": datetime.utcnow().isoformat()
                }
                append_login_event(admin_event)
                try_db_log(admin_event)

            secret_test = st.text_input("Test DB user (admin only)", value="")
            if secret_test:
                st.write("Admin-only action recorded (placeholder).")
                admin_event = {
                    "username": user_key,
                    "display_name": name,
                    "action": "secret_test",
                    "value_present": bool(secret_test),
                    "time": datetime.utcnow().isoformat()
                }
                append_login_event(admin_event)
                try_db_log(admin_event)

    # --- DB info display (no secrets printed) ---
    st.sidebar.markdown("### Connection Info")
