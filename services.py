# services.py — publicdash-safe version
import os
import pandas as pd
from sqlalchemy import create_engine, text

class Services:
    def __init__(self):
        dburl = os.getenv("DATABASE_URL")
        if not dburl:
            raise RuntimeError("DATABASE_URL not set in environment")
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
        return os.getenv("USER", "public")

    def now_iso(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
