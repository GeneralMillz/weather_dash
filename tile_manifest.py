import os

# ─────────────────────────────────────────────
# Weather-focused layout
# ─────────────────────────────────────────────
TILES = {
    "left": [
        "forecast_summary",
        "forecast_vs_bracket",
    ],
    "mid": [
        "model_outputs",
        "model_confidence_heatmap",
    ],
    "right": [
        "model_freshness",
    ],
    "summary": [
        "pipeline_self_audit",
        "schema_coverage_audit",
    ],
    "admin": [],
    "fun": [            # new tab for lightweight public games
        "rps_app",      # Rock Paper Scissors single-file app
    ],
}

# ─────────────────────────────────────────────
# Admin-only tiles (gated by INTERNAL_MODE)
# ─────────────────────────────────────────────
if os.getenv("INTERNAL_MODE") == "1":
    TILES["admin"].extend([
        "resource_tile",
    ])

# ─────────────────────────────────────────────
# Tab labels (used in app.py)
# ─────────────────────────────────────────────
TAB_LABELS = {
    "left": "🌡️ Forecasts",
    "mid": "🧪 Models",
    "right": "📍 Observations",
    "summary": "🧭 Summary",
    "admin": "🛠️ Admin",
    "fun": "🎮 Games",     # label for the new tab
}
