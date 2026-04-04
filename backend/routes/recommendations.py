"""
routes/recommendations.py — Association rule-based product recommendations.

Endpoints:
  GET  /api/recommendations/<item_id>     → "Frequently Bought Together"
  POST /api/recommendations/compare       → Compare Apriori vs FP-Growth
  GET  /api/recommendations/rules         → Return top association rules
"""
import json
import os
from flask import Blueprint, jsonify, request, current_app
from models import db, Item
from ml.preprocessing import load_raw_data, get_cached_cleaned_sales, build_transaction_matrix
from ml.apriori_module import run_apriori
from ml.fpgrowth_module import run_fpgrowth

recs_bp = Blueprint("recommendations", __name__)

# Simple in-memory cache so we don't re-run ML on every request
_cache = {}


def _get_rules(algorithm: str = "fpgrowth") -> dict:
    """
    Load or compute association rules. Results are cached.
    Backed by a JSON file for persistence across restarts.
    """
    cache_key = f"rules_{algorithm}"
    cache_file = current_app.config.get("CACHE_FILE", "")

    # 1. Check in-memory cache
    if cache_key in _cache:
        return _cache[cache_key]

    # 2. Check disk cache
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                all_cache = json.load(f)
            if cache_key in all_cache:
                _cache[cache_key] = all_cache[cache_key]
                return _cache[cache_key]
        except Exception:
            pass

    # 3. Compute fresh
    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        return {"rules": [], "frequent_itemsets": [], "n_rules": 0}
    basket = build_transaction_matrix(cleaned, max_items=200)

    cfg = current_app.config
    if algorithm == "apriori":
        result = run_apriori(
            basket,
            min_support=cfg.get("MIN_SUPPORT", 0.02),
            min_confidence=cfg.get("MIN_CONFIDENCE", 0.2),
            min_lift=cfg.get("MIN_LIFT", 1.0),
            max_rules=cfg.get("MAX_RULES", 50),
        )
    else:
        result = run_fpgrowth(
            basket,
            min_support=cfg.get("MIN_SUPPORT", 0.02),
            min_confidence=cfg.get("MIN_CONFIDENCE", 0.2),
            min_lift=cfg.get("MIN_LIFT", 1.0),
            max_rules=cfg.get("MAX_RULES", 50),
        )

    _cache[cache_key] = result

    # Persist to disk
    if cache_file:
        try:
            existing = {}
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    existing = json.load(f)
            existing[cache_key] = result
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump(existing, f)
        except Exception as e:
            print(f"[recommendations] Cache write failed: {e}")

    return result


def _enrich_rule_with_names(rule: dict) -> dict:
    """Add item names to antecedents and consequents."""
    def _names(ids):
        names = []
        for iid in ids:
            item = Item.query.get(int(iid))
            names.append(item.name[:60] if item else f"Item {iid}")
        return names

    enriched = dict(rule)
    enriched["antecedent_names"] = _names(rule.get("antecedents", []))
    enriched["consequent_names"] = _names(rule.get("consequents", []))
    return enriched


# ── GET /api/recommendations/<item_id> ───────────────────────────────────────
@recs_bp.route("/api/recommendations/<int:item_id>", methods=["GET"])
def get_recommendations(item_id):
    """
    Return 'Frequently Bought Together' items for a given product.
    Uses FP-Growth rules (faster) by default.
    Query param: algorithm = 'fpgrowth' | 'apriori'
    """
    algo = request.args.get("algorithm", "fpgrowth")
    result = _get_rules(algo)
    item_id_str = str(item_id)

    # Find rules where item_id appears in antecedents
    matching = [
        r for r in result.get("rules", [])
        if item_id_str in [str(x) for x in r.get("antecedents", [])]
    ]

    # Return top 5 consequents
    recs = []
    seen_items = set()
    for rule in matching[:10]:
        for cid in rule.get("consequents", []):
            if cid not in seen_items:
                item = Item.query.get(int(cid))
                if item:
                    recs.append(
                        {
                            "item_id": int(cid),
                            "name": item.name,
                            "avg_price": item.avg_price,
                            "confidence": rule["confidence"],
                            "lift": rule["lift"],
                        }
                    )
                    seen_items.add(cid)
        if len(recs) >= 5:
            break

    return jsonify(
        {
            "item_id": item_id,
            "recommendations": recs,
            "algorithm": algo.upper(),
        }
    )


# ── GET /api/recommendations/rules ───────────────────────────────────────────
@recs_bp.route("/api/recommendations/rules", methods=["GET"])
def get_rules():
    """Return all top association rules (with item names)."""
    algo = request.args.get("algorithm", "fpgrowth")
    result = _get_rules(algo)
    rules = result.get("rules", [])[:20]  # top 20 for display

    # Enrich with item names (limited to avoid slow queries)
    enriched = []
    for rule in rules:
        try:
            enriched.append(_enrich_rule_with_names(rule))
        except Exception:
            enriched.append(rule)

    return jsonify(
        {
            "rules": enriched,
            "n_rules": result.get("n_rules", 0),
            "n_itemsets": result.get("n_itemsets", 0),
            "execution_time_ms": result.get("execution_time_ms", 0),
            "algorithm": algo.upper(),
        }
    )


# ── POST /api/recommendations/compare ─────────────────────────────────────────
@recs_bp.route("/api/recommendations/compare", methods=["POST"])
def compare_algorithms():
    """
    Run both Apriori and FP-Growth and return a side-by-side comparison
    of execution times and number of rules/itemsets found.
    """
    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        return jsonify({"error": "No sales data available"}), 500
    basket = build_transaction_matrix(cleaned, max_items=150)

    cfg = current_app.config
    kwargs = dict(
        min_support=cfg.get("MIN_SUPPORT", 0.02),
        min_confidence=cfg.get("MIN_CONFIDENCE", 0.2),
        min_lift=cfg.get("MIN_LIFT", 1.0),
        max_rules=cfg.get("MAX_RULES", 50),
    )

    apriori_result = run_apriori(basket, **kwargs)
    fpgrowth_result = run_fpgrowth(basket, **kwargs)

    return jsonify(
        {
            "comparison": {
                "apriori": {
                    "execution_time_ms": apriori_result["execution_time_ms"],
                    "n_itemsets": apriori_result["n_itemsets"],
                    "n_rules": apriori_result["n_rules"],
                },
                "fpgrowth": {
                    "execution_time_ms": fpgrowth_result["execution_time_ms"],
                    "n_itemsets": fpgrowth_result["n_itemsets"],
                    "n_rules": fpgrowth_result["n_rules"],
                },
                "speedup": round(
                    apriori_result["execution_time_ms"]
                    / max(fpgrowth_result["execution_time_ms"], 0.001),
                    2,
                ),
            },
            "top_rules_apriori": apriori_result["rules"][:5],
            "top_rules_fpgrowth": fpgrowth_result["rules"][:5],
        }
    )
