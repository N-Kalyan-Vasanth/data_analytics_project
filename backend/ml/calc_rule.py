import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(__file__))

from preprocessing import get_cached_cleaned_sales, build_transaction_matrix
from apriori_module import run_apriori

def get_real_rule():
    df = get_cached_cleaned_sales()
    if df.empty:
        print("Data is empty.")
        return
        
    basket = build_transaction_matrix(df, group_by='shop_month', max_items=50)
    res = run_apriori(basket, min_support=0.01, min_confidence=0.1)
    
    print(f"Total Transactions (N): {len(basket)}")
    if not res['rules']:
        print("No rules found.")
        return
        
    for rule in res['rules'][:1]:
        print(f"Rule: {rule['antecedents']} -> {rule['consequents']}")
        print(f"Support: {rule['support']}")
        print(f"Confidence: {rule['confidence']}")
        print(f"Lift: {rule['lift']}")

        # Calculate exact counts
        ant = list(rule['antecedents'])
        con = list(rule['consequents'])
        
        # Count transactions containing antecedents
        ant_mask = basket[ant].all(axis=1)
        # Count transactions containing consequents
        con_mask = basket[con].all(axis=1)
        # Count both
        both_mask = ant_mask & con_mask
        
        print(f"Freq(A): {ant_mask.sum()}")
        print(f"Freq(B): {con_mask.sum()}")
        print(f"Freq(A U B): {both_mask.sum()}")
        
        # Provide sample rows
        # We can extract the raw CSV rows for these transaction IDs
        sample_txns = basket[both_mask].index[:3].tolist()
        sample_ant_only = basket[ant_mask & ~con_mask].index[:2].tolist()
        
        print(f"\nSample transactions with both A and B:")
        for t in sample_txns:
            print(t, df[df['transaction_id'] == t][['transaction_id_orig', 'item_id', 'item_name']].to_dict('records'))

if __name__ == '__main__':
    get_real_rule()
