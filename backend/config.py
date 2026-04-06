"""
config.py — Application configuration
Sets up database URI, CORS origins, and ML cache settings.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ── SQLite database stored in backend/db/ecommerce.db ──────────────────
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'db', 'ecommerce.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Data directory (CSVs live here) ─────────────────────────────────────
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # ── CORS allowed origins ─────────────────────────────────────────────────
    _extra = os.environ.get("FRONTEND_URL", "")
    CORS_ORIGINS = list(filter(None, [
        "http://localhost:5173",
        "http://localhost:3000",
        _extra,
    ]))

    # ── ML result cache file (JSON) ──────────────────────────────────────────
    CACHE_FILE = os.path.join(BASE_DIR, "db", "ml_cache.json")

    # ── Apriori / FP-Growth thresholds ───────────────────────────────────────
    MIN_SUPPORT = 0.02
    MIN_CONFIDENCE = 0.2
    MIN_LIFT = 1.0
    MAX_RULES = 50          # max association rules to return

    # ── Time-series config ───────────────────────────────────────────────────
    ARIMA_ORDER = (1, 1, 1)  # (p, d, q)
    FORECAST_MONTHS = 3      # months to forecast beyond last data point

    # ── Sequential pattern mining ────────────────────────────────────────────
    SEQ_MIN_SUPPORT = 0.0005   # minimum support for PrefixSpan
