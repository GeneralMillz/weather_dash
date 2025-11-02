import os

# ─────────────────────────────────────────────
# Weather-focused layout
# ─────────────────────────────────────────────
TILES = {
    "left": [
        "forecast_summary",             # Tomorrow's high temps
        "forecast_vs_bracket",          # Bracket alignment
    ],
    "mid": [
        "model_outputs",                # Model predictions
        "model_confidence_heatmap",     # Confidence histogram
    ],
    "right": [
        "observation_provenance",       # Source of today's observations
        "model_freshness",              # Last model run timestamp
    ],
    "summary": [
        "pipeline_self_audit",          # Status.json summary
        "schema_coverage_audit",        # Index/key coverage
    ],
    "admin": []
}

# ─────────────────────────────────────────────
# Admin-only tiles (gated by INTERNAL_MODE)
# ─────────────────────────────────────────────
if os.getenv("INTERNAL_MODE") == "1":
    TILES["admin"].extend([
        "resource_tile",                # System metrics (CPU, RAM, etc.)
        "loader_freshness",            # Recent ingest freshness
        "partition_health",            # Partition coverage
        "forecast_accuracy_extended",  # Forecast vs observed error
    ])

# ─────────────────────────────────────────────
# Tab labels (used in app.py)
# ─────────────────────────────────────────────
TAB_LABELS = {
    "left": "🌡️ Forecasts",
    "mid": "🧪 Models",
    "right": "📍 Observations",
    "summary": "🧭 Summary",
    "admin": "🛠️ Admin"
}
