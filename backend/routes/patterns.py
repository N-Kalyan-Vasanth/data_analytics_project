"""
routes/patterns.py — Sequential Pattern Mining API (PrefixSpan).

Endpoints:
  GET  /api/patterns/sequential        → all mined sequential patterns
  GET  /api/patterns/next/<item_id>    → "Customers also buy next" recs
  GET  /api/patterns/summary           → pattern mining summary stats
"""
import json
import os
from flask import Blueprint, jsonify, request, current_app
from models import Item
from ml.preprocessing import load_raw_data, get_cached_cleaned_sales, build_sequences
from ml.sequential_module import run_prefixspan, get_next_item_recommendations

patterns_bp = Blueprint("patterns", __name__)

# In-memory cache
_seq_cache = None
_patterns_cache = None


def _get_patterns():
    global _seq_cache, _patterns_cache

    if _patterns_cache is not None:
        return _patterns_cache

    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        return {"patterns": [], "n_sequences": 0, "n_patterns": 0}
    sequences = build_sequences(cleaned, n_shops=50, max_items=100)
    _seq_cache = sequences

    result = run_prefixspan(
        sequences,
        min_support=current_app.config.get("SEQ_MIN_SUPPORT", 0.01),
        max_pattern_len=4,
        max_results=100,
    )
    _patterns_cache = result
    return result


def _enrich_pattern(pattern_entry: dict) -> dict:
    """Add item names to each element in the pattern."""
    enriched = dict(pattern_entry)
    named_pattern = []
    for itemset in pattern_entry.get("pattern", []):
        names = []
        for iid in itemset:
            item = Item.query.get(int(iid))
            names.append({"id": int(iid), "name": item.name[:60] if item else f"Item {iid}"})
        named_pattern.append(names)
    enriched["named_pattern"] = named_pattern
    return enriched


# ── GET /api/patterns/sequential ─────────────────────────────────────────────
@patterns_bp.route("/api/patterns/sequential", methods=["GET"])
def get_sequential_patterns():
    """
    Return top sequential patterns mined from purchase history.
    Query params:
      - limit (int, default 20)
      - min_support (float, default from config)
    """
    limit = request.args.get("limit", 20, type=int)
    result = _get_patterns()

    patterns = result.get("patterns", [])[:limit]

    # Enrich top 10 patterns with item names (DB lookups are slow)
    enriched = []
    for i, p in enumerate(patterns):
        if i < 10:
            try:
                enriched.append(_enrich_pattern(p))
            except Exception:
                enriched.append(p)
        else:
            enriched.append(p)

    return jsonify(
        {
            "patterns": enriched,
            "n_patterns": result.get("n_patterns", 0),
            "n_sequences": result.get("n_sequences", 0),
            "algorithm": "PrefixSpan",
            "min_support": result.get("min_support", 0.01),
        }
    )


# ── GET /api/patterns/next/<item_id> ─────────────────────────────────────────
@patterns_bp.route("/api/patterns/next/<int:item_id>", methods=["GET"])
def get_next_recommendations(item_id):
    """
    Return 'Customers also buy next' recommendations based on sequential patterns.
    """
    result = _get_patterns()
    patterns = result.get("patterns", [])

    recs = get_next_item_recommendations(patterns, [item_id], top_n=5)

    # Enrich with item names
    enriched_recs = []
    for rec in recs:
        item = Item.query.get(int(rec["item_id"]))
        enriched_recs.append(
            {
                "item_id": rec["item_id"],
                "name": item.name if item else f"Item {rec['item_id']}",
                "avg_price": item.avg_price if item else 0,
                "score": rec["score"],
            }
        )

    return jsonify(
        {
            "item_id": item_id,
            "next_recommendations": enriched_recs,
            "algorithm": "PrefixSpan",
        }
    )


# ── GET /api/patterns/summary ─────────────────────────────────────────────────
@patterns_bp.route("/api/patterns/summary", methods=["GET"])
def get_patterns_summary():
    """Return high-level stats about the sequential pattern mining run."""
    result = _get_patterns()
    return jsonify(
        {
            "n_sequences": result.get("n_sequences", 0),
            "n_patterns": result.get("n_patterns", 0),
            "algorithm": "PrefixSpan",
            "min_support": result.get("min_support", 0.01),
        }
    )
