import streamlit as st
import pandas as pd

def render(services, st, state):
    st.subheader("📐 Forecast vs Bracket")
    try:
        df = services.query_df("""
            SELECT market_id, forecast_temp, observed_temp,
                   (observed_temp - forecast_temp) AS delta,
                   CASE WHEN ABS(observed_temp - forecast_temp) <= 2 THEN 'Aligned' ELSE 'Misaligned' END AS alignment
            FROM analytics.forecast_vs_observed
            WHERE ts > now() - interval '1 day'
            LIMIT 100
        """)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Bracket comparison failed: {e}")
