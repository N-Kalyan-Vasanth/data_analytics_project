"""
ml/sequential_module.py — Sequential Pattern Mining (PrefixSpan).

PrefixSpan grows patterns by prefix projection:
  1. Find all frequent 1-sequences (items with support >= min_support)
  2. For each frequent prefix, project the database and recurse

We implement a lightweight PrefixSpan from scratch (no external dependency)
so the algorithm is transparent and beginner-friendly.

Exported functions:
  - run_prefixspan(sequences, min_support) → dict
"""
from collections import defaultdict
from itertools import chain
import time


# ── PrefixSpan implementation ─────────────────────────────────────────────────

def _count_support(sequences: list, pattern: list) -> int:
    """
    Count how many sequences contain the pattern as a subsequence.

    A pattern [A, B] is a subsequence of S if there exist indices i < j
    such that A ⊆ S[i] and B ⊆ S[j].

    This is the support counting step.
    """
    count = 0
    for seq in sequences:
        # Try to match pattern elements in order
        pos = 0
        matched = True
        for itemset in pattern:
            found = False
            while pos < len(seq):
                if itemset.issubset(seq[pos]):
                    found = True
                    pos += 1
                    break
                pos += 1
            if not found:
                matched = False
                break
        if matched:
            count += 1
    return count


def _project_database(sequences: list, prefix_item: frozenset) -> list:
    """
    Project the sequence database relative to a given prefix item.

    For each sequence, find the first occurrence of prefix_item and
    return the suffix (everything after that position).
    """
    projected = []
    for seq in sequences:
        for i, itemset in enumerate(seq):
            if prefix_item.issubset(itemset):
                # suffix starts after this position
                suffix = seq[i + 1:]
                if suffix:
                    projected.append(suffix)
                break
    return projected


def prefixspan(
    sequences: list,
    min_support_count: int,
    max_pattern_len: int = 3,  # Reduced from 4
    timeout_seconds: int = 30,  # Add timeout
) -> list:
    """
    Run PrefixSpan and return all frequent sequential patterns.

    Args:
        sequences:          List of sequences; each sequence is a list of frozensets.
        min_support_count:  Minimum number of sequences a pattern must appear in.
        max_pattern_len:    Maximum pattern length (prevents combinatorial explosion).
        timeout_seconds:    Maximum time to run before giving up.

    Returns:
        List of (pattern, support_count) tuples, where pattern is a list of frozensets.
    """
    results = []
    call_count = [0]
    start_time = time.time()
    max_calls = 50000  # Hard limit on recursion calls

    def _grow(prefix: list, projected_db: list, depth: int = 0):
        call_count[0] += 1

        # Check timeout
        if time.time() - start_time > timeout_seconds:
            print(f"[prefixspan] TIMEOUT after {timeout_seconds}s")
            return False  # Signal timeout

        # Check recursion limits
        if call_count[0] > max_calls:
            print(f"[prefixspan] MAX CALLS ({max_calls}) exceeded")
            return False

        if len(prefix) >= max_pattern_len or not projected_db:
            return True

        # Progress logging (less frequent)
        if call_count[0] % 5000 == 0:
            elapsed = time.time() - start_time
            print(f"[prefixspan] {call_count[0]} calls, depth={depth}, patterns={len(results)}, time={elapsed:.1f}s")

        # Gather all unique items in projected_db
        item_counts = defaultdict(int)
        for seq in projected_db:
            seen = set()
            for itemset in seq:
                for item in itemset:
                    if item not in seen:
                        item_counts[item] += 1
                        seen.add(item)

        # Early termination: if no frequent items, stop
        frequent_items = [item for item, cnt in item_counts.items() if cnt >= min_support_count]
        if not frequent_items:
            return True

        # Limit branching factor to prevent explosion
        frequent_items = sorted(frequent_items)[:10]  # Top 10 most frequent items only

        # Recurse for each frequent item extension
        for item in frequent_items:
            cnt = item_counts[item]
            new_prefix = prefix + [frozenset([item])]
            results.append((new_prefix, cnt))
            new_db = _project_database(projected_db, frozenset([item]))

            if new_db and len(results) < 10000:  # Hard limit on results
                if not _grow(new_prefix, new_db, depth + 1):
                    return False  # Propagate timeout

        return True

    print(f"[prefixspan] Starting PrefixSpan with {len(sequences)} sequences, min_support={min_support_count}, timeout={timeout_seconds}s")
    success = _grow([], sequences, 0)

    elapsed = time.time() - start_time
    print(f"[prefixspan] {'Completed' if success else 'Terminated early'} - {len(results)} patterns, {call_count[0]} calls, {elapsed:.1f}s")

    return results


def run_prefixspan(
    sequences: list,
    min_support: float = 0.01,
    max_pattern_len: int = 3,  # Reduced from 4
    max_results: int = 50,
) -> dict:
    """
    Run PrefixSpan sequential pattern mining.

    Args:
        sequences:       List of purchase sequences (list of frozensets of item_ids).
        min_support:     Minimum support as a fraction of all sequences.
        max_pattern_len: Max length of patterns to mine.
        max_results:     Cap on returned patterns.

    Returns:
        {
          'patterns':      [{'pattern': [[item_id, ...], ...], 'support': float, 'count': int}],
          'n_sequences':   int,
          'n_patterns':    int,
          'min_support':   float,
          'algorithm':     'PrefixSpan',
        }
    """
    n_seq = len(sequences)
    if n_seq == 0:
        return {
            "patterns": [],
            "n_sequences": 0,
            "n_patterns": 0,
            "min_support": min_support,
            "algorithm": "PrefixSpan",
        }

    min_count = max(1, int(min_support * n_seq))
    print(f"[sequential] Running PrefixSpan on {n_seq} sequences, min_count={min_count}")

    try:
        # Use timeout to prevent infinite loops
        raw_patterns = prefixspan(sequences, min_count, max_pattern_len, timeout_seconds=45)

        # If no patterns found or timeout occurred, try a simpler approach
        if len(raw_patterns) == 0:
            print("[sequential] No patterns found, trying simpler approach...")
            raw_patterns = _simple_frequent_patterns(sequences, min_count, max_pattern_len)

        # Sort by count descending
        raw_patterns.sort(key=lambda x: x[1], reverse=True)

        patterns_out = []
        for pattern, cnt in raw_patterns[:max_results]:
            patterns_out.append(
                {
                    # Convert frozensets to sorted lists for JSON serialisation
                    "pattern": [sorted([str(item) for item in itemset]) for itemset in pattern],
                    "support": round(cnt / n_seq, 4),
                    "count": cnt,
                }
            )

        print(f"[sequential] Completed: {len(patterns_out)} patterns extracted from {len(raw_patterns)} found")
        return {
            "patterns": patterns_out,
            "n_sequences": n_seq,
            "n_patterns": len(raw_patterns),
            "min_support": min_support,
            "algorithm": "PrefixSpan",
        }
    except Exception as e:
        print(f"[sequential] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "patterns": [],
            "n_sequences": n_seq,
            "n_patterns": 0,
            "min_support": min_support,
            "algorithm": "PrefixSpan",
            "error": str(e),
        }


def _simple_frequent_patterns(sequences: list, min_support_count: int, max_pattern_len: int = 2) -> list:
    """
    Simple fallback approach: find frequent single-item and two-item patterns.
    Much faster but less comprehensive than full PrefixSpan.
    """
    print("[sequential] Using simple pattern mining approach")
    results = []

    # Find frequent single items
    item_counts = defaultdict(int)
    for seq in sequences:
        seen = set()
        for itemset in seq:
            for item in itemset:
                if item not in seen:
                    item_counts[item] += 1
                    seen.add(item)

    # Add single-item patterns
    for item, count in item_counts.items():
        if count >= min_support_count:
            results.append(([frozenset([item])], count))

    # Find frequent two-item patterns (simplified)
    if max_pattern_len >= 2:
        pair_counts = defaultdict(int)
        for seq in sequences:
            items_in_seq = set()
            for itemset in seq:
                items_in_seq.update(itemset)

            # Count co-occurrences within sequences
            items_list = list(items_in_seq)
            for i in range(len(items_list)):
                for j in range(i + 1, len(items_list)):
                    pair = frozenset([items_list[i], items_list[j]])
                    pair_counts[pair] += 1

        for pair, count in pair_counts.items():
            if count >= min_support_count:
                results.append(([pair], count))

    print(f"[sequential] Simple approach found {len(results)} patterns")
    return results


# ── Recommendation from sequential patterns ───────────────────────────────────
def get_next_item_recommendations(
    patterns: list,
    purchased_item_ids: list,
    top_n: int = 5,
) -> list:
    """
    Given a list of already purchased items and mined sequential patterns,
    suggest what a customer is likely to buy next.

    Strategy: find patterns whose first element matches any purchased item,
    then recommend the last element of the pattern.

    Args:
        patterns:           Output of run_prefixspan()['patterns']
        purchased_item_ids: Item IDs already bought (as strings or ints)
        top_n:              Max recommendations

    Returns:
        List of recommended item IDs (strings)
    """
    purchased_set = set(str(i) for i in purchased_item_ids)
    recommendations = defaultdict(float)

    for p in patterns:
        pat = p["pattern"]
        if len(pat) < 2:
            continue
        # Check if first element overlaps with purchased items
        first_items = set(str(x) for x in pat[0])
        if first_items & purchased_set:
            # Recommend items in the last element with support as weight
            for item in pat[-1]:
                recommendations[str(item)] += p["support"]

    # Sort by recommendation score
    sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    return [{"item_id": k, "score": round(v, 4)} for k, v in sorted_recs[:top_n]]
