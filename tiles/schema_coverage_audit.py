import streamlit as st
import pandas as pd

def render(services, st, state):
    st.subheader("🧩 Schema Coverage Audit")
    try:
        df = services.query_df("""
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog','information_schema')
            ORDER BY table_schema, table_name
        """)
        summary = df.groupby(["table_schema", "table_name"]).size().reset_index(name="column_count")
        st.dataframe(summary, use_container_width=True)
    except Exception as e:
        st.error(f"Schema coverage failed: {e}")
