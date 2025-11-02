from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
from datetime import date

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Helper: Check and Load Secrets Safely ---
# Required secret keys list (documented)
REQUIRED_SECRETS = [
    "admin_username", "admin_email", "admin_password",
    "viewer_username", "viewer_email", "viewer_password"
]

# Check required secrets early and stop with a clear message if any are missing
missing = [k for k in REQUIRED_SECRETS if st.secrets.get(k) is None]
if missing:
    st.sidebar.error("Streamlit Secrets missing required keys: " + ", ".join(missing))
    st.stop()

# --- Load all credentials and optional DB secrets from secrets safely ---
# Required
ADMIN_USERNAME = st.secrets.get("admin_username")
ADMIN_EMAIL = st.secrets.get("admin_email")
ADMIN_PASSWORD = st.secrets.get("admin_password")

VIEWER_USERNAME = st.secrets.get("viewer_username")
VIEWER_EMAIL = st.secrets.get("viewer_email")
VIEWER_PASSWORD = st.secrets.get("viewer_password")

# Optional DB creds for non-critical logging
DB_USER = st.secrets.get("db_user", "")
DB_PASS = st.secrets.get("db_pass", "")
DB_HOST = st.secrets.get("db_host", "localhost")
DB_PORT = int(st.secrets.get("db_port", "5432"))
DB_NAME = st.secrets.get("db_name", "postgres") # Default to postgres

# --- Build credentials dictionary (no personal info in code) ---
credentials = {
    "usernames": {
        ADMIN_USERNAME: {
            "email": ADMIN_EMAIL,
            "name": "Admin",
            "password": ADMIN_PASSWORD
        },
        VIEWER_USERNAME: {
            "email": VIEWER_EMAIL,
            "name": "Viewer",
            "password": VIEWER_PASSWORD
        }
    }
}

# --- Authenticator setup ---
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",     # cookie name
    "dashboard_signature",  # signature key
    cookie_expiry_days=7
)

# --- Role utility ---
def is_viewer(username_key: Optional[str]) -> bool:
    """Checks if the logged-in user key corresponds to the Viewer account."""
    return username_key == VIEWER_USERNAME

# --- Logging utilities (no secrets ever logged) ---
LOG_PATH = os.environ.get("DASHBOARD_LOGIN_LOG", "login_events.jsonl")

def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    """Safely append a JSON line, ensuring no secrets are present."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    except Exception:
        # ignore directory creation failures
        pass

    # Redact sensitive keys explicitly (even though they shouldn't be passed in)
    safe = {k: v for k, v in record.items() if not k.endswith("password")}

    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, default=str) + "\n")
    except Exception:
        # If file logging fails, surface a non-sensitive warning in the sidebar
        try:
            st.sidebar.warning("Login logging file write failed.")
        except Exception:
            pass

def try_db_log(event: Dict[str, Any]) -> None:
    """Optional: write login event to DB if DB creds provided. Fails silently."""
    if not (DB_USER and DB_PASS and DB_NAME):
        return
    try:
        # This dependency must be installed externally (e.g., via a requirements.txt)
        import psycopg2

        # Use connection details from st.secrets
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=2
        )
        cur = conn.cursor()
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_login_events (
                id SERIAL PRIMARY KEY,
                username TEXT,
                display_name TEXT,
                login_time TIMESTAMP WITH TIME ZONE,
                station TEXT,
                selected_date DATE,
                is_viewer BOOLEAN,
                action TEXT,
                override_value TEXT
            )
        """)
        conn.commit()

        # Insert the event data
        cur.execute(
            """
            INSERT INTO user_login_events (username, display_name, login_time, station, selected_date, is_viewer, action, override_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event.get("username"),
                event.get("display_name"),
                event.get("login_time"),
                event.get("station"),
                event.get("selected_date"),
                event.get("is_viewer"),
                event.get("action"),
                event.get("override_value"),
            )
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # intentionally silent to avoid breaking the app if DB logging isn't configured or fails
        # print(f"DB Log Failed: {e}")
        return

# --- Main app flow ---
# The stauth.Authenticate object handles the UI/cookie logic when called without arguments
display_name, auth_status, user_key = authenticator.login("Login", "main")

# --- Authenticated session ---
if auth_status:
    login_time = datetime.now(timezone.utc).isoformat()

    # Sidebar: session info and logout
    st.sidebar.markdown(f"**User**: {user_key or 'unknown'}")
    st.sidebar.markdown(f"**Role**: {display_name or 'user'}")
    st.sidebar.markdown(f"**Login (UTC)**: {login_time}")

    try:
        authenticator.logout("Logout", "sidebar")
    except Exception:
        pass # Logout button may fail if not fully initialized, ignore
    
    st.sidebar.success(f"Welcome, {display_name}!")

    # Title and short notice
    st.title("Secure Dashboard")
    st.markdown("✅ Deployment OK. Viewer accounts are read-only; Admin accounts have controls.")

    # --- Read-only Filters (station + date) ---
    st.sidebar.header("Filters")
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"], index=0)
    # Default to today for a slightly more realistic feel
    selected_date = st.sidebar.date_input("Select Date", date.today())

    # Log event (initial login metadata)
    event = {
        "username": user_key,
        "display_name": display_name,
        "login_time": login_time,
        "station": station,
        "selected_date": selected_date.strftime("%Y-%m-%d"),
        "is_viewer": is_viewer(user_key),
        "action": "login",
        "override_value": None # Only used for admin actions
    }
    append_jsonl(LOG_PATH, event)
    try_db_log(event) # Attempt DB log non-blocking

    # --- Forecast vs Observed Comparison (read-only) ---
    st.header("Forecast vs Observed Comparison")

    # Placeholder data for demonstration
    forecast_data = {
        "KDTW": {"forecast": 42, "observed": 40},
        "KGRR": {"forecast": 39, "observed": 41},
        "KLAN": {"forecast": 41, "observed": 38}
    }

    f = forecast_data.get(station, {"forecast": None, "observed": None})
    delta, bracket, alignment = None, None, None

    try:
        if f["forecast"] is not None and f["observed"] is not None:
            delta = f["observed"] - f["forecast"]
            # Creating a bracket for the forecast value
            bracket_cut = pd.cut([f["forecast"]], bins=[-100, 35, 40, 45, 100], labels=["<35", "35–40", "40–45", ">45"])
            bracket = bracket_cut[0]
            alignment = "Aligned" if abs(delta) <= 2 else "Misaligned"
    except Exception:
        # Safely handle missing data or unexpected types
        pass

    comp_df = pd.DataFrame([{
        "Station": station,
        "Date": selected_date.strftime("%Y-%m-%d"),
        "Forecast Temp": f["forecast"],
        "Observed Temp": f["observed"],
        "Delta": delta,
        "Bracket": bracket,
        "Alignment": alignment
    }])
    st.dataframe(comp_df, use_container_width=True)

    # --- Bracket ROI Simulator (read-only) ---
    st.header("Bracket ROI Simulator")
    roi_df = pd.DataFrame({
        "Bracket": ["35–40", "40–45", "45–50"],
        "Entry Price": [0.40, 0.45, 0.50],
        "Exit Price": [0.48, 0.42, 0.55],
        "Position": ["Long", "Short", "Long"]
    })
    roi_df["ROI"] = roi_df.apply(
        lambda row: (row["Exit Price"] - row["Entry Price"]) if row["Position"] == "Long"
        else (row["Entry Price"] - row["Exit Price"]), axis=1
    )
    st.dataframe(roi_df, use_container_width=True)

    # --- Kalshi Weather Market Snapshot (read-only) ---
    st.header("Kalshi Weather Market Snapshot")
    kalshi_df = pd.DataFrame({
        "Market": [
            "Will it snow in Detroit?",
            "High temp > 45°F in Grand Rapids?",
            "Rain in Lansing?"
        ],
        "Price Yes": [0.42, 0.65, 0.30],
        "Price No": [0.58, 0.35, 0.70],
        "Sentiment": ["Rising", "Stable", "Volatile"]
    })
    st.dataframe(kalshi_df, use_container_width=True)

    # --- Mini Chart: Temp Over Time (read-only) ---
    st.header("Temperature Trend (Past 10 Days)")
    try:
        # Inject current data point into a placeholder series
        ft = f.get("forecast", None)
        ot = f.get("observed", None)
        
        # Use simple placeholder arrays that end with the current filter's data point
        forecast_series = [41, 42, 43, 44, 42, 40, 39, 41, 42] + ([ft] if ft is not None else [40])
        observed_series = [40, 41, 42, 43, 41, 39, 38, 40, 41] + ([ot] if ot is not None else [41])

        trend_df = pd.DataFrame({
            "Date": pd.date_range(end=selected_date, periods=10),
            "Forecast Temp": forecast_series[-10:],
            "Observed Temp": observed_series[-10:]
        })
        fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Temperature trend unavailable.")


    # --- Read-only notice for viewer accounts; admin sees controls ---
    if is_viewer(user_key):
        st.info("🔒 Read-only mode. Interactive controls are disabled for Viewer accounts.")
    else:
        st.header("Admin Controls")

        with st.expander("Ingestion Controls"):
            run_ingest = st.button("Run ingestion")
            if run_ingest:
                st.success("Ingestion started (placeholder).")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "action": "run_ingest",
                    "time": datetime.now(timezone.utc).isoformat()
                }
                append_jsonl(LOG_PATH, admin_event)
                try_db_log(admin_event)

            override_station = st.text_input("Override station ID (e.g., KORD)", value="")
            if st.button("Queue override") and override_station:
                st.write(f"Override queued for station: {override_station}")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "action": "override_station",
                    "override_value": override_station,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                append_jsonl(LOG_PATH, admin_event)
                try_db_log(admin_event)

        with st.expander("Manual Actions"):
            run_backfill = st.button("Run backfill")
            if run_backfill:
                st.success("Backfill started (placeholder).")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "action": "run_backfill",
                    "time": datetime.now(timezone.utc).isoformat()
                }
                append_jsonl(LOG_PATH, admin_event)
                try_db_log(admin_event)

            secret_test = st.text_input("Test value for audit log", value="test_value")
            if st.button("Record admin test"):
                st.write("Admin-only action recorded.")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "action": "admin_test",
                    "value_present": bool(secret_test),
                    "time": datetime.now(timezone.utc).isoformat()
                }
                # Note: 'secret_test' value itself is NOT logged, only its presence/absence
                append_jsonl(LOG_PATH, admin_event)
                try_db_log(admin_event)

    # --- DB info display (no secrets printed) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Logging Status")
    st.sidebar.write(f"File logging path: `{LOG_PATH}`")
    st.sidebar.write("DB user configured" if DB_USER else "DB user: NOT CONFIGURED")


elif auth_status is False:
    st.error("Invalid username/password.")
else:
    # Not logged in yet (auth_status is None)
    st.info("Please log in to access the dashboard.")
