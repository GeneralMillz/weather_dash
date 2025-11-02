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
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime
import json
import os

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Load secrets (prefer Streamlit secrets; fallback to env) ---
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    # Do not reveal whether a specific secret exists; we just use it
    try:
        return st.secrets.get(key) if hasattr(st, "secrets") else os.environ.get(key, default)
    except Exception:
        return os.environ.get(key, default)

ADMIN_USERNAME = get_secret("admin_username")
ADMIN_EMAIL = get_secret("admin_email")
ADMIN_PASSWORD = get_secret("admin_password")

VIEWER_USERNAME = get_secret("viewer_username")
VIEWER_EMAIL = get_secret("viewer_email")
VIEWER_PASSWORD = get_secret("viewer_password")

# Optional DB creds for non-critical logging
DB_USER = get_secret("db_user", "")
DB_PASS = get_secret("db_pass", "")
DB_HOST = get_secret("db_host", "localhost")
DB_PORT = int(get_secret("db_port", "5432"))
DB_NAME = get_secret("db_name", "")

# Minimal UI-friendly display name mapping (no PII in code)
ROLE_LABELS = {"admin": "Admin", "viewer": "Viewer"}

# --- Authentication shim (lightweight, avoids dependency issues) ---
# If streamlit_authenticator is available, prefer that; otherwise fallback to a minimal prompt.
_auth_backend = None
try:
    import streamlit_authenticator as stauth  # type: ignore
    _auth_backend = "stauth"
except Exception:
    _auth_backend = "fallback"

def build_credentials() -> Dict[str, Any]:
    usernames = {}
    if ADMIN_USERNAME and ADMIN_EMAIL and ADMIN_PASSWORD:
        usernames[ADMIN_USERNAME] = {"email": ADMIN_EMAIL, "name": ROLE_LABELS["admin"], "password": ADMIN_PASSWORD}
    if VIEWER_USERNAME and VIEWER_EMAIL and VIEWER_PASSWORD:
        usernames[VIEWER_USERNAME] = {"email": VIEWER_EMAIL, "name": ROLE_LABELS["viewer"], "password": VIEWER_PASSWORD}
    return {"usernames": usernames}

credentials = build_credentials()

# If stauth present, use it for cookie-based login; otherwise present fallback username/password entry.
authenticator = None
if _auth_backend == "stauth" and credentials["usernames"]:
    authenticator = stauth.Authenticate(credentials, "dashboard_cookie", "dashboard_signature", cookie_expiry_days=7)

def login() -> tuple[Optional[str], Optional[bool], Optional[str]]:
# --- Helper: fail-safe secret loader ---
def require_secret(key: str):
    val = st.secrets.get(key) if isinstance(st.secrets, dict) else None
    if not val:
        st.sidebar.error(f"Missing required secret: {key}")
        st.stop()
    return val

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

# --- Load credentials and DB secrets from secrets safely ---
admin_username = st.secrets.get("admin_username")
admin_email = st.secrets.get("admin_email")
admin_password = st.secrets.get("admin_password")

viewer_username = st.secrets.get("viewer_username")
viewer_email = st.secrets.get("viewer_email")
viewer_password = st.secrets.get("viewer_password")

# optional DB secrets (may be absent)
db_user = st.secrets.get("db_user", "")
db_pass = st.secrets.get("db_pass", "")

# --- Build credentials dictionary (no personal info in code) ---
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
# streamlit-authenticator expects (credentials, cookie_name, key, cookie_expiry_days)
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",       # cookie name
    "dashboard_signature",    # signature key
    cookie_expiry_days=7
)

# --- Login ---
name, auth_status, user_key = authenticator.login()

# --- Helper: check read-only ---
def is_viewer(u_key):
    return u_key == viewer_username

# --- Logging utilities ---
LOG_PATH = "login_events.log"

def append_login_event(event: dict):
    """
    Returns (display_name, auth_status, username_key)
    auth_status: True authorized, False invalid, None not attempted
    Append a JSON line to LOG_PATH. Does not log secrets.
    Handles empty dirname safely.
    """
    if authenticator:
        try:
            name, auth_status, user_key = authenticator.login("Login", "main")
            return name, auth_status, user_key
        except Exception:
            # fall through to fallback
            pass

    # Fallback manual prompt (non-persistent)
    st.markdown("### Login")
    u = st.text_input("Username", key="fallback_user")
    p = st.text_input("Password", type="password", key="fallback_pass")
    btn = st.button("Sign in", key="fallback_signin")
    if not btn:
        return None, None, None

    # Validate against available credentials without exposing details
    for k, v in credentials.get("usernames", {}).items():
        if u == k and p == v.get("password"):
            return v.get("name"), True, k
    return None, False, None

# --- Logging utilities (no secrets ever logged) ---
LOG_PATH = os.environ.get("DASHBOARD_LOGIN_LOG", "login_events.jsonl")

def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    """Safely append a JSON line. Always redact secrets before calling."""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        dirname = os.path.dirname(LOG_PATH)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
    except Exception:
        # ignore directory creation failures
        pass
    safe = {k: v for k, v in record.items() if k not in ("password", "db_pass", "admin_password")}

    event_line = json.dumps(event, default=str)
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, default=str) + "\n")
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(event_line + "\n")
    except Exception:
        # Surface a non-sensitive warning in UI if file can't be written
        # If file logging fails, surface a non-sensitive warning in the sidebar
        try:
            st.sidebar.warning("Unable to write login audit file.")
            st.sidebar.warning("Login logging file write failed.")
        except Exception:
            pass

def try_db_log(event: Dict[str, Any]) -> None:
    """Optional: write login event to DB if DB creds provided. Fails silently."""
    if not (DB_USER and DB_PASS and DB_NAME):
def try_db_log(event: dict):
    """
    Optional: attempt to write login event to a DB if psycopg2 is available and db_user/db_pass present.
    This is non-blocking and will fail silently on missing dependencies or connectivity.
    """
    if not db_user or not db_pass:
        return
    try:
        import psycopg2  # type: ignore
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT, connect_timeout=2)
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboard_user_login_events (
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_login_events (
                id SERIAL PRIMARY KEY,
                username TEXT,
                display_name TEXT,
@@ -139,190 +129,198 @@ def try_db_log(event: Dict[str, Any]) -> None:
                selected_date DATE,
                is_viewer BOOLEAN
            )
            """
        )
        """)
        conn.commit()
        cur.execute(
            "INSERT INTO dashboard_user_login_events (username, display_name, login_time, station, selected_date, is_viewer) VALUES (%s,%s,%s,%s,%s,%s)",
            (
                event.get("username"),
                event.get("display_name"),
                event.get("login_time"),
                event.get("station"),
                event.get("selected_date"),
                event.get("is_viewer"),
            ),
            "INSERT INTO user_login_events (username, display_name, login_time, station, selected_date, is_viewer) VALUES (%s,%s,%s,%s,%s,%s)",
            (event.get("username"), event.get("display_name"), event.get("login_time"), event.get("station"), event.get("selected_date"), event.get("is_viewer"))
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        # intentionally silent to avoid breaking the app
        # intentionally silent to avoid breaking the app if DB logging isn't configured
        return

# --- Role utility ---
def is_viewer(username_key: Optional[str]) -> bool:
    return username_key == VIEWER_USERNAME

# --- Main app flow ---
display_name, auth_status, user_key = login()

# --- Authenticated session ---
if auth_status:
    login_time = datetime.now(timezone.utc).isoformat()
    # Sidebar: session info (no secrets)
    st.sidebar.markdown(f"**User**: {user_key or 'unknown'}")
    # Record basic login metadata (no secrets)
    login_time = datetime.utcnow().isoformat()
    # Minimal sidebar info for the current session; user sees timestamp but not secrets
    st.sidebar.markdown(f"**User**: {user_key}")
    st.sidebar.markdown(f"**Login (UTC)**: {login_time}")

    # If using stauth, show logout control
    if authenticator:
        try:
            authenticator.logout("Logout", "sidebar")
        except Exception:
            pass
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    st.sidebar.success(f"Logged in as {display_name or 'user'}")

    # Title and short notice
    st.title("Secure Dashboard")
    st.markdown("✅ Deployment OK. Viewer accounts are read-only; admin accounts have controls.")
    st.markdown("✅ Deploy works. Read-only weather dashboard is enabled for viewer accounts.")

    # --- Filters ---
    # --- Read-only Filters (station + date) ---
    st.sidebar.header("Filters")
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"], index=0)
    selected_date = st.sidebar.date_input("Select Date", pd.to_datetime("2025-10-27"))
    station = st.sidebar.selectbox("Select Station", ["KDTW", "KGRR", "KLAN"])
    # ensure date_input gets a date object default
    selected_date = st.sidebar.date_input("Select Date", pd.to_datetime("2025-10-27").date())

    # Log event (no secrets included)
    # Log the login event (and current filters) to file and optionally DB
    event = {
        "username": user_key,
        "display_name": display_name,
        "display_name": name,
        "login_time": login_time,
        "station": station,
        "selected_date": selected_date.strftime("%Y-%m-%d"),
        "is_viewer": is_viewer(user_key),
        "is_viewer": is_viewer(user_key)
    }
    append_jsonl(LOG_PATH, event)
    # Append to local log
    append_login_event(event)
    # Attempt DB log non-blocking
    try_db_log(event)

    # --- Forecast vs Observed (placeholder data kept non-sensitive) ---
    # --- Forecast vs Observed Comparison (read-only) ---
    st.header("Forecast vs Observed Comparison")

    # Placeholder / sample data; replace with live fetch from NOAA or DB when ready
    forecast_data = {
        "KDTW": {"forecast": 42, "observed": 40},
        "KGRR": {"forecast": 39, "observed": 41},
        "KLAN": {"forecast": 41, "observed": 38},
        "KLAN": {"forecast": 41, "observed": 38}
    }

    f = forecast_data.get(station, {"forecast": None, "observed": None})
    delta = None
    bracket = None
    alignment = None
    if f["forecast"] is not None and f["observed"] is not None:
        delta = f["observed"] - f["forecast"]
        bracket = pd.cut([f["forecast"]], bins=[-100, 35, 40, 45, 100], labels=["<35", "35–40", "40–45", "45–50"])[0]
        alignment = "Aligned" if abs(delta) <= 2 else "Misaligned"
    comp_df = pd.DataFrame(
        [
            {
                "Station": station,
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Forecast Temp": f["forecast"],
                "Observed Temp": f["observed"],
                "Delta": delta,
                "Bracket": bracket,
                "Alignment": alignment,
            }
        ]
    )
        try:
            delta = f["observed"] - f["forecast"]
            bracket = pd.cut([f["forecast"]], bins=[-100, 35, 40, 45, 100], labels=["<35", "35–40", "40–45", "45–50"])[0]
            alignment = "Aligned" if abs(delta) <= 2 else "Misaligned"
        except Exception:
            delta = None
            bracket = None
            alignment = None

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

    # --- ROI simulator (read-only) ---
    # --- Bracket ROI Simulator (read-only) ---
    st.header("Bracket ROI Simulator")
    roi_df = pd.DataFrame(
        {
            "bracket": ["35–40", "40–45", "45–50"],
            "entry_price": [0.40, 0.45, 0.50],
            "exit_price": [0.48, 0.42, 0.55],
            "position": ["Long", "Short", "Long"],
        }
    roi_df = pd.DataFrame({
        "bracket": ["35–40", "40–45", "45–50"],
        "entry_price": [0.40, 0.45, 0.50],
        "exit_price": [0.48, 0.42, 0.55],
        "position": ["Long", "Short", "Long"]
    })
    roi_df["ROI"] = roi_df.apply(
        lambda row: (row["exit_price"] - row["entry_price"]) if row["position"] == "Long"
        else (row["entry_price"] - row["exit_price"]), axis=1
    )
    roi_df["ROI"] = roi_df.apply(lambda row: (row["exit_price"] - row["entry_price"]) if row["position"] == "Long" else (row["entry_price"] - row["exit_price"]), axis=1)
    st.dataframe(roi_df, use_container_width=True)

    # --- Market snapshot (non-sensitive) ---
    # --- Kalshi Weather Market Snapshot (read-only) ---
    st.header("Kalshi Weather Market Snapshot")
    kalshi_df = pd.DataFrame(
        {
            "Market": ["Will it snow in Detroit?", "High temp > 45°F in Grand Rapids?", "Rain in Lansing?"],
            "Price Yes": [0.42, 0.65, 0.30],
            "Price No": [0.58, 0.35, 0.70],
            "Sentiment": ["Rising", "Stable", "Volatile"],
        }
    )
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

    # --- Mini chart ---
    # --- Mini Chart: Temp Over Time (read-only) ---
    st.header("Temperature Trend (Past 10 Days)")
    trend_df = pd.DataFrame(
        {
    # guard missing forecast/observed values in trend arrays
    try:
        ft = f.get("forecast", None)
        ot = f.get("observed", None)
        forecast_series = [41, 42, 43, 44, 42, 40, 39, 41, 42, ft]
        observed_series = [40, 41, 42, 43, 41, 39, 38, 40, 41, ot]
        trend_df = pd.DataFrame({
            "Date": pd.date_range(end=selected_date, periods=10),
            "Forecast Temp": [41, 42, 43, 44, 42, 40, 39, 41, 42, f["forecast"]],
            "Observed Temp": [40, 41, 42, 43, 41, 39, 38, 40, 41, f["observed"]],
        }
    )
    fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
    st.plotly_chart(fig, use_container_width=True)
            "Forecast Temp": forecast_series,
            "Observed Temp": observed_series
        })
        fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Temperature trend unavailable.")

    # --- Read-only / Admin controls ---
    # --- Read-only notice for viewer accounts; admin sees controls ---
    if is_viewer(user_key):
        st.info("🔒 Read-only mode. Interactive controls are disabled for this user.")
    else:
        st.header("Admin Controls")
        st.header("Admin Controls (hidden from viewers)")
        with st.expander("Ingestion Controls"):
            run_ingest = st.button("Run ingestion (admin only)")
            run_ingest = st.button("Run ingestion")
            if run_ingest:
                st.success("Ingestion started (placeholder).")
                admin_event = {"username": user_key, "display_name": display_name, "action": "run_ingest", "time": datetime.now(timezone.utc).isoformat()}
                append_jsonl(LOG_PATH, admin_event)
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
            if st.button("Queue override") and override_station:
                st.write("Override queued for station:", override_station)
            if override_station:
                st.write(f"Override queued for station: {override_station}")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "display_name": name,
                    "action": "override_station",
                    "override_value": override_station,
                    "time": datetime.now(timezone.utc).isoformat(),
                    "time": datetime.utcnow().isoformat()
                }
                append_jsonl(LOG_PATH, admin_event)
                append_login_event(admin_event)
                try_db_log(admin_event)

        with st.expander("Manual Actions"):
            run_backfill = st.button("Run backfill (admin only)")
            run_backfill = st.button("Run backfill")
            if run_backfill:
                st.success("Backfill started (placeholder).")
                admin_event = {"username": user_key, "display_name": display_name, "action": "run_backfill", "time": datetime.now(timezone.utc).isoformat()}
                append_jsonl(LOG_PATH, admin_event)
                admin_event = {
                    "username": user_key,
                    "display_name": name,
                    "action": "run_backfill",
                    "time": datetime.utcnow().isoformat()
                }
                append_login_event(admin_event)
                try_db_log(admin_event)

            secret_test = st.text_input("Test DB user (admin only)", value="")
            if st.button("Record admin test") and secret_test:
                st.write("Admin-only action recorded.")
            if secret_test:
                st.write("Admin-only action recorded (placeholder).")
                admin_event = {
                    "username": user_key,
                    "display_name": display_name,
                    "display_name": name,
                    "action": "secret_test",
                    "value_present": bool(secret_test),
                    "time": datetime.now(timezone.utc).isoformat(),
                    "time": datetime.utcnow().isoformat()
                }
                append_jsonl(LOG_PATH, admin_event)
                append_login_event(admin_event)
                try_db_log(admin_event)

    # --- DB-info (no secrets printed) ---
    # --- DB info display (no secrets printed) ---
    st.sidebar.markdown("### Connection Info")
    st.sidebar.write("DB user configured" if DB_USER else "DB user not configured")
    st.sidebar.write("DB password configured" if DB_PASS else "DB password not configured")
    st.sidebar.write("DB user configured" if db_user else "DB user not configured")
    st.sidebar.write("DB password configured" if db_pass else "DB password not configured")

elif auth_status is False:
    st.error("Invalid credentials")
else:
    # Not logged in yet
    st.info("Please log in to access the dashboard.")
