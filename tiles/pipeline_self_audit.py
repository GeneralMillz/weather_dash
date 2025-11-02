import os
import streamlit as st
import pandas as pd
import json
from pathlib import Path

def render(services, st, state):
    st.subheader("🧠 Pipeline Self-Audit")
    path = Path(os.getenv("STATUS_JSON", "./status/status.json"))
    if not path.exists():
        st.warning("No status.json found.")
        return
    try:
        data = json.loads(path.read_text())
        totals = data.get("totals", {})
        st.json(totals)
        runs = pd.DataFrame(data.get("last_runs", []))
        if not runs.empty:
            st.dataframe(runs, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to parse status.json: {e}")
