from __future__ import annotations
import streamlit as st
import json, os
from datetime import datetime, timezone
from tile_manifest import TILES, TAB_LABELS
from services import Services
from auth import (
    init_authenticator,
    login_ui,
    logout_ui,
    is_viewer,
    get_user_role,
    session_info
)

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="Kalshi Weather Cockpit", layout="wide")
st.markdown("# 🧭 Kalshi Weather Cockpit")
st.caption("Public dashboard — viewer-safe tiles only")

# ─────────────────────────────────────────────
# Auth setup
# ─────────────────────────────────────────────
authenticator = init_authenticator()
name, auth_status, user_key = login_ui(authenticator)

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
    login_time = session_info(user_key, name)
    logout_ui(authenticator, name)

    # Log login event
    append_login_event({
        "username": user_key,
        "display_name": name,
        "login_time": login_time,
        "role": get_user_role(user_key)
    })

    # ─────────────────────────────────────────────
    # Services and shared state
    # ─────────────────────────────────────────────
    try:
        services = Services()
    except Exception as e:
        st.error("❌ Failed to initialize services.")
        st.exception(e)  # Show the real error
        st.stop()

    state = {
        "user": user_key,
        "now_iso": lambda: login_time,
        "role": get_user_role(user_key)
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
                    st.exception(e)

else:
    if auth_status is False:
        st.error("Invalid credentials")
    else:
        st.info("Please log in to access the dashboard.")
