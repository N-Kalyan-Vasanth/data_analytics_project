"""
routes/patterns.py — Sequential Pattern Mining API (PrefixSpan).

Endpoints:
  GET  /api/patterns/sequential        → all mined sequential patterns
  GET  /api/patterns/next/<item_id>    → "Customers also buy next" recs
  GET  /api/patterns/summary           → pattern mining summary stats
"""
import json
import os
import time
from flask import Blueprint, jsonify, request, current_app
from models import Item, db
from ml.preprocessing import load_raw_data, get_cached_cleaned_sales, build_sequences
from ml.sequential_module import run_prefixspan, get_next_item_recommendations

patterns_bp = Blueprint("patterns", __name__)

# In-memory cache
_seq_cache = None
_patterns_cache = None
_cache_time = None
_CACHE_TTL = 3600  # Cache for 1 hour


def _get_patterns():
    global _seq_cache, _patterns_cache, _cache_time

    # Return cached result if still valid
    if _patterns_cache is not None and _cache_time is not None:
        elapsed = time.time() - _cache_time
        if elapsed < _CACHE_TTL:
            print(f"[patterns] Returning cached patterns (age: {elapsed:.1f}s)")
            return _patterns_cache

    print("[patterns] Cache miss - rebuilding patterns...")
    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        print("[patterns] No cleaned sales data available")
        return {"patterns": [], "n_sequences": 0, "n_patterns": 0}
    
    # Increase limits for better pattern generation
    sequences = build_sequences(cleaned, n_shops=500, max_items=200)
    if not sequences:
        print("[patterns] No sequences built")
        return {"patterns": [], "n_sequences": 0, "n_patterns": 0}
    
    _seq_cache = sequences

    result = run_prefixspan(
        sequences,
        min_support=current_app.config.get("SEQ_MIN_SUPPORT", 0.01),
        max_pattern_len=4,
        max_results=100,
    )
    
    _patterns_cache = result
    _cache_time = time.time()
    print(f"[patterns] Cache updated at {_cache_time}")
    return result


def _enrich_pattern(pattern_entry: dict) -> dict:
    """Add item names to each element in the pattern using a single efficient query."""
    enriched = dict(pattern_entry)
    named_pattern = []
    
    # Collect all unique item IDs
    all_ids = set()
    for itemset in pattern_entry.get("pattern", []):
        all_ids.update(itemset)
    
    # Fetch all items in one query
    if all_ids:
        items = db.session.query(Item).filter(Item.id.in_(list(all_ids))).all()
        item_map = {item.id: item.name for item in items}
    else:
        item_map = {}
    
    # Build named pattern using the map
    for itemset in pattern_entry.get("pattern", []):
        names = []
        for iid in itemset:
            item_name = item_map.get(iid, f"Item {iid}")
            # Ensure proper encoding
            if isinstance(item_name, str):
                item_name = item_name.encode('utf-8', errors='replace').decode('utf-8')
            names.append({"id": str(iid), "name": item_name[:60]})
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

    # Enrich top 15 patterns with item names (batch fetch is now efficient)
    enriched = []
    for i, p in enumerate(patterns):
        if i < 15:
            try:
                enriched.append(_enrich_pattern(p))
            except Exception as e:
                print(f"[patterns] Error enriching pattern {i}: {e}")
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
@patterns_bp.route("/api/patterns/next/<string:item_id>", methods=["GET"])
def get_next_purchase_patterns(item_id):
    """
    Return 'Customers also buy next' recommendations based on sequential patterns.
    """
    result = _get_patterns()
    patterns = result.get("patterns", [])

    recs = get_next_item_recommendations(patterns, [item_id], top_n=5)

    # Enrich with item names
    enriched_recs = []
    for rec in recs:
        item = Item.query.get(str(rec["item_id"]))
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
