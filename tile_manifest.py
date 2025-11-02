# tile_manifest.py — publicdash manifest
import os

# ─────────────────────────────────────────────
# Column layout (left/mid/right)
# ─────────────────────────────────────────────
TILES = {
    "left": [
        "forecast_summary",
        "signal_divergence",
    ],
    "mid": [
        "model_outputs",
        "schema_coverage_audit",
    ],
    "right": [
        "forecast_vs_bracket",
        "model_confidence_heatmap",
    ],
    "summary": [
        "dashboard_status",
        "forecast_accuracy_summary",
    ],
    "admin": []
}

# ─────────────────────────────────────────────
# Conditional admin tiles (internal only)
# ─────────────────────────────────────────────
if os.getenv("INTERNAL_MODE") == "1":
    TILES["admin"].append("resource_tile")
    TILES["admin"].append("simulate_launcher")  # example internal tile
    TILES["admin"].append("run_model")          # example internal tile

# ─────────────────────────────────────────────
# Optional: tab labels (used in app.py)
# ─────────────────────────────────────────────
TAB_LABELS = {
    "left": "🧬 Signals",
    "mid": "📊 Models",
    "right": "📈 Forecasts",
    "summary": "🧭 Summary",
    "admin": "🛠️ Admin"
}
