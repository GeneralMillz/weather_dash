import streamlit as st
import pandas as pd
import json
import os

def render(services, st, state):
    st.subheader("🌡️ Forecast Summary (Tomorrow)")
    path = os.getenv("FORECAST_JSON", "./out/high_temp_forecast.json")
    try:
        with open(path, "r") as f:
            raw = json.load(f)
        data = [{"city": k, "tmax": v} for k, v in raw.items()] if isinstance(raw, dict) else raw
        df = pd.DataFrame(data).sort_values("tmax", ascending=False)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load forecast: {e}")
