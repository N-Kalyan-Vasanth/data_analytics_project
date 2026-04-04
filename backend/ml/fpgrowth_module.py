"""
ml/fpgrowth_module.py — FP-Growth Association Rule Mining.

Uses mlxtend's fpgrowth() + association_rules().
Identical interface to apriori_module so they can be compared side-by-side.

Exported functions:
  - run_fpgrowth(basket_df, min_support, min_confidence, min_lift) → dict
"""
import time
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules


def run_fpgrowth(
    basket_df: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.2,
    min_lift: float = 1.0,
    max_rules: int = 50,
) -> dict:
    """
    Run the FP-Growth algorithm on a one-hot basket DataFrame.

    FP-Growth builds a compact FP-Tree structure and traverses it to find
    frequent itemsets — generally much faster than Apriori on large datasets
    because it scans the data only twice.

    Args:
        basket_df:      Boolean DataFrame (rows=transactions, cols=item_ids)
        min_support:    Minimum support threshold (0–1)
        min_confidence: Minimum confidence threshold (0–1)
        min_lift:       Minimum lift threshold
        max_rules:      Cap the number of rules returned

    Returns:
        Same schema as apriori_module.run_apriori(), plus 'algorithm' key.
    """
    start = time.perf_counter()

    # ── Step 1: Frequent itemsets via FP-Growth ────────────────────────────
    freq_itemsets = fpgrowth(
        basket_df,
        min_support=min_support,
        use_colnames=True,
        max_len=3,
    )

    if freq_itemsets.empty:
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "frequent_itemsets": [],
            "rules": [],
            "execution_time_ms": round(elapsed, 2),
            "n_itemsets": 0,
            "n_rules": 0,
            "algorithm": "FP-Growth",
        }

    # ── Step 2: Association rules ──────────────────────────────────────────
    rules = association_rules(
        freq_itemsets,
        metric="confidence",
        min_threshold=min_confidence,
    )

    # ── Step 3: Filter by lift ─────────────────────────────────────────────
    rules = rules[rules["lift"] >= min_lift]
    rules = rules.sort_values("lift", ascending=False).head(max_rules)

    elapsed = (time.perf_counter() - start) * 1000

    # ── Serialise ──────────────────────────────────────────────────────────
    itemsets_out = [
        {
            "itemset": sorted(list(row["itemsets"])),
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
        "frequent_itemsets": itemsets_out[:100],
        "rules": rules_out,
        "execution_time_ms": round(elapsed, 2),
        "n_itemsets": len(freq_itemsets),
        "n_rules": len(rules),
        "algorithm": "FP-Growth",
    }
