import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(__file__))

from preprocessing import load_raw_data, clean_sales, build_transaction_matrix, build_sequences, aggregate_monthly
from apriori_module import run_apriori
from fpgrowth_module import run_fpgrowth
from timeseries_module import run_timeseries
from sequential_module import run_prefixspan

def perform_sample_analysis():
    print("--- 1. Loading and Sampling Data ---")
    data = load_raw_data()
    sales_df = data['sales']
    
    # Take a sample for fast processing
    sample_df = sales_df.head(10000).copy()
    cleaned_sample = clean_sales(sample_df)
    
    print(f"Sample size: {len(cleaned_sample)} rows")
    print("\nSample Values (First 5 Rows):")
    print(cleaned_sample.head(5).to_string())
    
    print("\n--- 2. Association Rule Mining (Apriori vs FP-Growth) ---")
    basket = build_transaction_matrix(cleaned_sample, group_by='shop_month', max_items=20)
    
    apriori_res = run_apriori(basket, min_support=0.01, min_confidence=0.1)
    fpgrowth_res = run_fpgrowth(basket, min_support=0.01, min_confidence=0.1)
    
    print(f"Apriori found {apriori_res['n_rules']} rules in {apriori_res['execution_time_ms']}ms")
    print(f"FP-Growth found {fpgrowth_res['n_rules']} rules in {fpgrowth_res['execution_time_ms']}ms")
    
    if apriori_res['rules']:
        print("\nExample Association Rules (Apriori/FP-Growth):")
        for rule in apriori_res['rules'][:3]:
            print(f"Rule: {rule['antecedents']} -> {rule['consequents']}")
            print(f"  Support: {rule['support']}, Confidence: {rule['confidence']}, Lift: {rule['lift']}")

    print("\n--- 3. Time Series Analysis (ARIMA vs Moving Average) ---")
    monthly_agg = aggregate_monthly(cleaned_sample)
    if len(monthly_agg) < 5:
        print("Note: Sample size too small for meaningful ARIMA, using more data from main sales_df...")
        full_monthly = aggregate_monthly(clean_sales(sales_df.head(100000)))
        ts_res = run_timeseries(full_monthly, arima_order=(1, 1, 1), forecast_months=3)
    else:
        ts_res = run_timeseries(monthly_agg, arima_order=(1, 1, 1), forecast_months=3)

    print("\nARIMA Predictions (Next 3 Months):")
    for f in ts_res['arima'].get('forecast', []):
        print(f"  Month: {f['month']}, Predicted Sales: {f['predicted']}")

    print("\n--- 4. Sequential Pattern Matching (PrefixSpan) ---")
    sequences = build_sequences(cleaned_sample, n_shops=5, max_items=20)
    seq_res = run_prefixspan(sequences, min_support=0.001)
    
    print(f"PrefixSpan found {seq_res['n_patterns']} sequential patterns")
    if seq_res['patterns']:
        print("\nExample Sequential Patterns:")
        for pat in seq_res['patterns'][:3]:
            print(f"Pattern: {pat['pattern']}, Support: {pat['support']}")

if __name__ == "__main__":
    perform_sample_analysis()
