import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Load credentials and DB secrets from secrets ---
# Required keys in Streamlit Secrets:
# admin_username, admin_email, admin_password,
# viewer_username, viewer_email, viewer_password,
# db_user, db_pass
admin_username = st.secrets["admin_username"]
admin_email = st.secrets["admin_email"]
admin_password = st.secrets["admin_password"]

viewer_username = st.secrets["viewer_username"]
viewer_email = st.secrets["viewer_email"]
viewer_password = st.secrets["viewer_password"]

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

# --- Authenticator setup (no deprecated parameters) ---
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

    st.title("Secure Dashboard")
    st.markdown("✅ Deploy works. Read-only weather dashboard is enabled for viewer accounts.")

    # --- Read-only Filters (station + date) ---
    st.sidebar.header("Filters")
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

    # Placeholder / sample data; replace with live fetch from NOAA or DB when ready
    forecast_data = {
        "KDTW": {"forecast": 42, "observed": 40},
        "KGRR": {"forecast": 39, "observed": 41},
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
        "bracket": ["35–40", "40–45", "45–50"],
        "entry_price": [0.40, 0.45, 0.50],
        "exit_price": [0.48, 0.42, 0.55],
        "position": ["Long", "Short", "Long"]
    })
    roi_df["ROI"] = roi_df.apply(
        lambda row: (row["exit_price"] - row["entry_price"]) if row["position"] == "Long"
        else (row["entry_price"] - row["exit_price"]), axis=1
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
    trend_df = pd.DataFrame({
        "Date": pd.date_range(end=selected_date, periods=10),
        "Forecast Temp": [41, 42, 43, 44, 42, 40, 39, 41, 42, f["forecast"]],
        "Observed Temp": [40, 41, 42, 43, 41, 39, 38, 40, 41, f["observed"]]
    })
    fig = px.line(trend_df, x="Date", y=["Forecast Temp", "Observed Temp"], title=f"{station} Temperature Trend")
    st.plotly_chart(fig, use_container_width=True)

    # --- Read-only notice for viewer accounts; admin sees controls ---
    if is_viewer(user_key):
        st.info("🔒 Read-only mode. Interactive controls are disabled for this user.")
    else:
        st.header("Admin Controls (hidden from viewers)")
        with st.expander("Ingestion Controls"):
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
    st.sidebar.write("DB user configured" if db_user else "DB user not configured")
    st.sidebar.write("DB password configured" if db_pass else "DB password not configured")

elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.info("Please log in to access the dashboard.")
