"""
ml/preprocessing.py — Data cleaning and transformation utilities.

Functions:
  - load_raw_data()            Load all CSVs into DataFrames
  - clean_sales()              Remove outliers, fix negatives
  - aggregate_monthly()        Daily → monthly sales
  - build_transaction_matrix() One-hot encoded basket per (shop,month)
  - build_sequences()          Ordered item sequences per shop
"""
import os
import json
import numpy as np
import pandas as pd
from functools import lru_cache

# ── Path helpers ──────────────────────────────────────────────────────────────
_DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _p(name: str) -> str:
    """Resolve a filename to the data directory path."""
    return os.path.join(_DATA, name)


# ── 1. Load raw CSVs ──────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_raw_data() -> dict:
    files = {
        "sales": "online_retail.csv",
    }
    data = {}
    for key, fname in files.items():
        path = _p(fname)
        if os.path.exists(path):
            data[key] = pd.read_csv(path, encoding='utf-8')
            print(f"[preprocessing] Loaded {fname}: {data[key].shape}")
        else:
            print(f"[preprocessing] WARNING: {fname} not found at {path}")
            data[key] = pd.DataFrame()
    return data


@lru_cache(maxsize=1)
def get_cached_cleaned_sales() -> pd.DataFrame:
    data = load_raw_data()
    if "sales" not in data or data["sales"].empty:
        return pd.DataFrame()
    return clean_sales(data["sales"])


# ── 2. Clean sales data ───────────────────────────────────────────────────────
def clean_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    df = sales_df.copy()

    # Drop missing values
    df.dropna(subset=['InvoiceDate', 'StockCode', 'Quantity', 'Price', 'Customer ID'], inplace=True)
    
    # Remove cancellations (Invoice starts with 'C')
    if 'Invoice' in df.columns:
        df['Invoice'] = df['Invoice'].astype(str)
        df = df[~df['Invoice'].str.startswith(('C', 'c'))]
    
    # Keep positive quantities only
    df = df[df["Quantity"] > 0]

    # Keep positive prices only
    df = df[df["Price"] > 0]

    # Remove extreme price outliers (top 1%)
    price_cap = df["Price"].quantile(0.99)
    df = df[df["Price"] <= price_cap]

    # Map the columns so downstream processes work exactly the same
    df.rename(columns={
        'Invoice': 'transaction_id_orig',
        'StockCode': 'item_id',
        'Description': 'item_name',
        'Quantity': 'item_cnt_day',
        'Price': 'item_price',
        'Customer ID': 'shop_id',
        'InvoiceDate': 'date'
    }, inplace=True)

    df['date'] = pd.to_datetime(df['date'])
    df['year_month_str'] = df["date"].dt.strftime("%Y-%m")

    df.reset_index(drop=True, inplace=True)
    print(f"[preprocessing] After cleaning: {df.shape[0]} rows")
    return df


# ── 3. Monthly aggregation ─────────────────────────────────────────────────────
def aggregate_monthly(sales_df: pd.DataFrame) -> pd.DataFrame:
    df = sales_df.copy()
    
    df["revenue"] = df["item_price"] * df["item_cnt_day"]

    monthly = (
        df.groupby("year_month_str")
        .agg(
            total_items=("item_cnt_day", "sum"),
            total_revenue=("revenue", "sum"),
        )
        .reset_index()
        .sort_values("year_month_str")
    )
    return monthly


def aggregate_monthly_by_item(sales_df: pd.DataFrame) -> pd.DataFrame:
    df = sales_df.copy()
    
    df["revenue"] = df["item_price"] * df["item_cnt_day"]

    monthly = (
        df.groupby(["year_month_str", "item_id"])
        .agg(
            total_items=("item_cnt_day", "sum"),
            total_revenue=("revenue", "sum"),
        )
        .reset_index()
    )
    return monthly


# ── 4. Transaction matrix for Apriori / FP-Growth ────────────────────────────
def build_transaction_matrix(
    sales_df: pd.DataFrame,
    group_by: str = "shop_day",
    max_items: int = 50,
) -> pd.DataFrame:
    df = sales_df.copy()

    # Select top N most-sold items to reduce matrix size
    top_items = (
        df.groupby("item_id")["item_cnt_day"]
        .sum()
        .nlargest(max_items)
        .index.tolist()
    )
    df = df[df["item_id"].isin(top_items)]

    # Create transaction key
    if group_by == "shop_month":
        df["transaction_id"] = (
            df["shop_id"].astype(str) + "_" + df["year_month_str"]
        )
    else:
        # Real Invoice number
        df["transaction_id"] = df["transaction_id_orig"].astype(str)

    # Pivot to one-hot matrix
    basket = (
        df.groupby(["transaction_id", "item_id"])["item_cnt_day"]
        .sum()
        .unstack(fill_value=0)
    )
    basket = (basket > 0).astype(bool)
    basket.columns = [str(c) for c in basket.columns]

    print(f"[preprocessing] Transaction matrix shape: {basket.shape}")
    return basket


# ── 5. Sequences for PrefixSpan ──────────────────────────────────────────────
def build_sequences(
    sales_df: pd.DataFrame,
    n_shops: int = 30,
    max_items: int = 50,
) -> list:
    df = sales_df.copy()
    print(f"[preprocessing] Building sequences from {len(df)} rows...")

    print(f"[preprocessing] Finding top {max_items} items by sales volume...")
    top_items = (
        df.groupby("item_id")["item_cnt_day"]
        .sum()
        .nlargest(max_items)
        .index.tolist()
    )
    df = df[df["item_id"].isin(top_items)]
    print(f"[preprocessing] Filtered to top {len(top_items)} items, {len(df)} rows remaining")

    shots = df["shop_id"].dropna().unique()
    shops = np.random.choice(shots, min(n_shops, len(shots)), replace=False) if len(shots) > 0 else []
    
    df = df[df["shop_id"].isin(shops)]
    print(f"[preprocessing] Using {len(shops)} shops, {len(df)} rows remaining")

    sequences = []
    for i, (shop_id, shop_df) in enumerate(df.groupby("shop_id")):
        if i % 10 == 0:
            print(f"[preprocessing] Processing shop {i+1}/{len(shops)}...")
        # Order by month
        shop_df = shop_df.sort_values("year_month_str")
        seq = []
        for _, month_df in shop_df.groupby("year_month_str"):
            itemset = frozenset(month_df["item_id"].unique())
            seq.append(itemset)
        if len(seq) >= 2:
            sequences.append(seq)

    print(f"[preprocessing] Built {len(sequences)} sequences from {len(shops)} shops")
    return sequences


# ── 6. Top selling items summary ──────────────────────────────────────────────
def get_top_items(sales_df: pd.DataFrame, items_df: pd.DataFrame = None, n: int = 10) -> list:
    top = (
        sales_df.groupby("item_id")["item_cnt_day"]
        .sum()
        .nlargest(n)
        .reset_index()
    )
    top.columns = ["item_id", "total_sold"]
    
    # Get descriptions
    desc_map = sales_df.drop_duplicates(subset=['item_id']).set_index('item_id')['item_name'].to_dict()
    top['item_name'] = top['item_id'].map(desc_map)

    return top.to_dict(orient="records")
