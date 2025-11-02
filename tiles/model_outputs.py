import streamlit as st
import pandas as pd
import plotly.express as px

def render(services, st, state):
    st.subheader("📊 Model Outputs")
    try:
        df = services.query_df("""
            SELECT market_id, model_prob, ts
            FROM analytics.model_outputs
            ORDER BY ts DESC
            LIMIT 500
        """)
        st.dataframe(df, use_container_width=True)
        df["bucket"] = pd.cut(df["model_prob"], bins=[0,0.25,0.5,0.75,1.0])
        dist = df.groupby("bucket").size().reset_index(name="count")
        fig = px.bar(dist, x="bucket", y="count", title="Model Probability Distribution")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Model query failed: {e}")
