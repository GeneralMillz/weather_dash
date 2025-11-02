import os
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st # <-- NEW: Import Streamlit to access st.secrets

class Services:
    def __init__(self):
        # 🔥 FIX: Retrieve the database URL from st.secrets, as defined in secrets.toml
        # This replaces the failing os.getenv() call.
        try:
            dburl = st.secrets["database"]["url"]
        except KeyError as e:
            # Handle the case where the structure is missing entirely
            raise RuntimeError(f"Database URL configuration missing in secrets.toml: {e}") from e

        if not dburl:
            raise RuntimeError("Database URL value is empty in secrets.toml.")
            
        # NOTE: If your database is not publicly accessible, this connection 
        # (even with the correct URL) will still fail on Streamlit Cloud.
        self.engine = create_engine(dburl, pool_pre_ping=True)

    def query_df(self, sql: str, params=None, limit=None):
        if limit:
            sql = f"{sql.strip().rstrip(';')} LIMIT {limit}"
        with self.engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})

    def get_conn(self):
        return self.engine.connect()

    def run_cmd(self, cmd: str, timeout: int = 10):
        # Stubbed out for publicdash — no shell access
        return 1, "", "run_cmd disabled in public mode"

    @property
    def user(self):
        # This still uses os.getenv, which might be fine if you set an external USER variable,
        # but if you intended to use the authenticated user, this should be accessed from the
        # app state (which is passed to tiles, but not directly accessible here).
        return os.getenv("USER", "public")

    def now_iso(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
