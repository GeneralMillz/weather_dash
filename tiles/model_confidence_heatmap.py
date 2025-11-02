import streamlit as st
import altair as alt
import pandas as pd

def render(services, st, state):
    st.subheader("🧪 Model Confidence Heatmap")
    try:
        df = services.query_df("""
            SELECT model_prob
            FROM analytics.model_outputs
            WHERE ts > now() - interval '1 day'
            LIMIT 500
        """)
        df["confidence"] = abs(df["model_prob"] - 0.5) * 2
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X("confidence:Q", bin=True),
            y="count()"
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"Confidence chart failed: {e}")
