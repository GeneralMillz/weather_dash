import streamlit as st

def render(services, st, state):
    st.subheader("🕒 Model Freshness")
    try:
        df = services.query_df("SELECT MAX(ts) AS last_model_run FROM analytics.model_outputs")
        st.metric("Last Model Run", str(df["last_model_run"].iloc[0]))
    except Exception as e:
        st.error(f"Freshness query failed: {e}")
