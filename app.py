import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px

# --- Page config ---
st.set_page_config(page_title="Secure Dashboard", layout="centered")

# --- Load credentials and DB secrets from secrets ---
# Make sure your Streamlit Secrets (Cloud or .streamlit/secrets.toml) include:
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

# --- Authenticated session ---
if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Logged in as {name}")

    st.title("Secure Dashboard")
    st.markdown("✅ Deploy works. Replace these tiles with your schema tiles, Kalshi ladder logic, or NOAA audit panels.")

    # Shared read-only widgets / tiles
    st.header("Schema Coverage Audit")
    schema_status = {
        "analytics.model_outputs": "OK",
        "analytics.weather_training": "OK",
        "market.market_ticks": "MISSING_INDEX",
        "simulator.trade_logs": "OK",
        "pipeline_runs": "OK"
    }
    schema_df = pd.DataFrame(list(schema_status.items()), columns=["table", "status"])
    st.dataframe(schema_df, use_container_width=True)

    st.header("Kalshi Ladder Snapshot")
    ladder = pd.DataFrame({
        "market": ["market_a", "market_b", "market_c"],
        "bracket": ["0.40–0.50", "0.65–0.75", "0.30–0.40"],
        "position": ["Long", "Short", "Long"],
        "sentiment": ["Rising", "Stable", "Volatile"]
    })
    st.dataframe(ladder, use_container_width=True)

    st.header("NOAA Forecast Audit (sample)")
    audit = pd.DataFrame({
        "station_id": ["STN1", "STN2", "STN3"],
        "forecast_temp": [42, 39, 41],
        "observed_temp": [40, 41, 38],
        "delta": [-2, 2, -3],
        "status": ["OK", "WARN", "WARN"]
    })
    st.dataframe(audit, use_container_width=True)

    # Example chart tile
    st.header("Sample Market Price Over Time")
    df = pd.DataFrame({
        "timestamp": pd.date_range(start="2025-10-01", periods=10, freq="D"),
        "price": [0.42, 0.45, 0.47, 0.44, 0.49, 0.51, 0.53, 0.50, 0.48, 0.52]
    })
    fig = px.line(df, x="timestamp", y="price", title="Sample Market Price Over Time")
    st.plotly_chart(fig, use_container_width=True)

    # --- Interactive controls only for admin (not viewer) ---
    if is_viewer(user_key):
        st.info("🔒 Read-only mode. Interactive controls are disabled for this user.")
    else:
        st.header("Admin Controls")
        with st.expander("Ingestion Controls"):
            run_ingest = st.button("Run ingestion")
            if run_ingest:
                st.success("Ingestion started (placeholder).")

            override_station = st.text_input("Override station ID", value="")
            if override_station:
                st.write(f"Override queued for station: {override_station}")

        with st.expander("Manual Actions"):
            run_backfill = st.button("Run backfill")
            if run_backfill:
                st.success("Backfill started (placeholder).")

            secret_test = st.text_input("Test DB user (admin only)", value="")
            if secret_test:
                st.write("Admin-only action recorded (placeholder).")

    # --- DB info display (no secrets printed) ---
    st.sidebar.markdown("### Connection Info")
    st.sidebar.write("DB user configured" if db_user else "DB user not configured")
    st.sidebar.write("DB password configured" if db_pass else "DB password not configured")

elif auth_status is False:
    st.error("Invalid credentials")
else:
    st.info("Please log in to access the dashboard.")
