"""
ml/apriori_module.py — Apriori Association Rule Mining.

Uses mlxtend's apriori() + association_rules() on a one-hot transaction matrix.
Measures and returns execution time for comparison with FP-Growth.

Exported functions:
  - run_apriori(basket_df, min_support, min_confidence, min_lift) → dict
"""
import time
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules


def run_apriori(
    basket_df: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.2,
    min_lift: float = 1.0,
    max_rules: int = 50,
) -> dict:
    """
    Run the Apriori algorithm on a one-hot basket DataFrame.

    Steps:
      1. Find frequent itemsets using apriori()
      2. Generate association rules from itemsets
      3. Filter by confidence and lift thresholds
      4. Sort by lift (descending)

    Args:
        basket_df:      Boolean DataFrame (rows=transactions, cols=item_ids)
        min_support:    Minimum support threshold (0–1)
        min_confidence: Minimum confidence threshold (0–1)
        min_lift:       Minimum lift threshold (>= 1 means positive correlation)
        max_rules:      Cap the number of rules returned

    Returns:
        {
          'frequent_itemsets': list of {itemset, support},
          'rules':             list of {antecedents, consequents, support,
                                        confidence, lift},
          'execution_time_ms': float,
          'n_itemsets':        int,
          'n_rules':           int,
        }
    """
    start = time.perf_counter()

    # ── Step 1: Frequent itemsets ──────────────────────────────────────────
    freq_itemsets = apriori(
        basket_df,
        min_support=min_support,
        use_colnames=True,  # keep item_id names as strings
        max_len=3,          # limit itemset size upwards to 3 for speed
    )

    if freq_itemsets.empty:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "frequent_itemsets": [],
            "rules": [],
            "execution_time_ms": round(elapsed, 2),
            "n_itemsets": 0,
            "n_rules": 0,
        }

    # ── Step 2: Association rules ──────────────────────────────────────────
    rules = association_rules(
        freq_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )

    # ── Step 3: Filter by lift ─────────────────────────────────────────────
    rules = rules[rules["lift"] >= min_lift]

    # ── Step 4: Sort by lift desc ──────────────────────────────────────────
    rules = rules.sort_values("lift", ascending=False).head(max_rules)

    elapsed = (time.perf_counter() - start) * 1000

    # ── Serialise results ──────────────────────────────────────────────────
    itemsets_out = [
        {
            "itemset": sorted(list(row["itemsets"])),  # frozenset → sorted list
            "support": round(row["support"], 4),
        }
        for _, row in freq_itemsets.iterrows()
    ]

    rules_out = [
        {
            "antecedents": sorted(list(row["antecedents"])),
            "consequents": sorted(list(row["consequents"])),
            "support": round(row["support"], 4),
            "confidence": round(row["confidence"], 4),
            "lift": round(row["lift"], 4),
        }
        for _, row in rules.iterrows()
    ]

    return {
        "frequent_itemsets": itemsets_out[:100],   # cap for JSON response
        "rules": rules_out,
        "execution_time_ms": round(elapsed, 2),
        "n_itemsets": len(freq_itemsets),
        "n_rules": len(rules),
    }
