from __future__ import annotations
import streamlit as st
import streamlit_authenticator as stauth
import json, os
from datetime import datetime, timezone
from tile_manifest import TILES, TAB_LABELS
from services import Services

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="Kalshi Weather Cockpit", layout="wide")
st.markdown("# 🧭 Kalshi Weather Cockpit")
st.caption("Public dashboard — viewer-safe tiles only")

# ─────────────────────────────────────────────
# Load credentials from secrets
# ─────────────────────────────────────────────
admin_username = st.secrets["admin_username"]
admin_email = st.secrets["admin_email"]
admin_password = st.secrets["admin_password"]

viewer_username = st.secrets["viewer_username"]
viewer_email = st.secrets["viewer_email"]
viewer_password = st.secrets["viewer_password"]

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
    authenticator.logout("Logout", "sidebar")
    st.sidebar.markdown(f"👤 **{name}** ({user_key})")
    st.sidebar.caption(f"🔒 Session started: {login_time[:16]} UTC")

    # Log login event
    event = {
        "username": user_key,
        "display_name": name,
        "login_time": login_time,
        "is_viewer": is_viewer(user_key)
    }
    append_login_event(event)

    # ─────────────────────────────────────────────
    # Services and shared state
    # ─────────────────────────────────────────────
    try:
        services = Services()
    except Exception as e:
        st.error("❌ Failed to initialize services.")
        st.stop()

    state = {
        "user": user_key,
        "now_iso": lambda: login_time
    }

    # ─────────────────────────────────────────────
    # Dashboard layout
    # ─────────────────────────────────────────────
    tab_keys = list(TILES.keys())
    tab_labels = [TAB_LABELS.get(k, k) for k in tab_keys]
    tabs = st.tabs(tab_labels)

    for i, tab in enumerate(tabs):
        with tab:
            for tile_name in TILES[tab_keys[i]]:
                try:
                    mod = __import__(f"tiles.{tile_name}", fromlist=["render"])
                    mod.render(services, st, state)
                except Exception as e:
                    st.error(f"❌ Tile `{tile_name}` failed: {e}")

else:
    if auth_status is False:
        st.error("Invalid credentials")
    else:
        st.info("Please log in to access the dashboard.")
