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
    """
    Load all CSV files into a dict of DataFrames.
    Caches the result in memory so subsequent calls are instant.

    Returns:
        {
          'sales':      DataFrame (main training set),
          'test':       DataFrame,
          'items':      DataFrame,
          'categories': DataFrame,
          'shops':      DataFrame,
        }
    """
    files = {
        "sales":      "sales_train.csv",
        "test":       "test.csv",
        "items":      "items.csv",
        "categories": "item_categories.csv",
        "shops":      "shops.csv",
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
    """Read and clean sales data once, cache it permanently in memory."""
    data = load_raw_data()
    if "sales" not in data or data["sales"].empty:
        return pd.DataFrame()
    return clean_sales(data["sales"])



# ── 2. Clean sales data ───────────────────────────────────────────────────────
def clean_sales(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw sales DataFrame:
      - Remove rows where item_cnt_day < 0 (refunds)
      - Remove rows where item_price <= 0
      - Remove extreme outliers (price > 99th percentile)
      - Parse the date column

    Args:
        sales_df: Raw sales DataFrame from sales_train.csv

    Returns:
        Cleaned DataFrame
    """
    df = sales_df.copy()

    # Keep positive quantities only
    df = df[df["item_cnt_day"] > 0]

    # Keep positive prices only
    df = df[df["item_price"] > 0]

    # Remove extreme price outliers (top 1%)
    price_cap = df["item_price"].quantile(0.99)
    df = df[df["item_price"] <= price_cap]

    # Skipping slow datetime parsing of 3 million rows (takes ~15s)
    # df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y", errors="coerce")
    # df.dropna(subset=["date"], inplace=True)

    df.reset_index(drop=True, inplace=True)
    print(f"[preprocessing] After cleaning: {df.shape[0]} rows")
    return df


# ── 3. Monthly aggregation ─────────────────────────────────────────────────────
def aggregate_monthly(sales_df: pd.DataFrame) -> pd.DataFrame:
    df = sales_df.copy()
    
    # Fast vectorized year-month from date_block_num
    y = 2013 + (df["date_block_num"] // 12)
    m = (df["date_block_num"] % 12) + 1
    df["year_month_str"] = y.astype(str) + "-" + m.astype(str).str.zfill(2)
    
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
    y = 2013 + (df["date_block_num"] // 12)
    m = (df["date_block_num"] % 12) + 1
    df["year_month_str"] = y.astype(str) + "-" + m.astype(str).str.zfill(2)
    
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
    group_by: str = "shop_month",
    max_items: int = 200,
) -> pd.DataFrame:
    """
    Build a boolean one-hot encoded basket matrix for association rule mining.

    Each row = one "transaction" (a shop in a given month).
    Each column = one item (True/False = bought or not bought).

    We limit to the top `max_items` most frequently bought items to keep
    the matrix manageable.

    Args:
        sales_df: Cleaned sales DataFrame
        group_by:  'shop_month' (default) or 'shop_day'
        max_items: How many of the most popular items to include

    Returns:
        Binary DataFrame (rows=transactions, cols=item_ids as strings)
    """
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
            df["shop_id"].astype(str) + "_" + df["date_block_num"].astype(str)
        )
    else:
        df["transaction_id"] = (
            df["shop_id"].astype(str)
            + "_"
            + df["date"].dt.strftime("%Y%m%d")
        )

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
    n_shops: int = 50,
    max_items: int = 100,
) -> list:
    """
    Build ordered purchase sequences per shop for sequential pattern mining.

    Each sequence = list of itemsets ordered by date_block_num (month).
    Each itemset = frozenset of item_ids bought that month by that shop.

    Args:
        sales_df: Cleaned sales DataFrame
        n_shops:  Limit to first N shops (for performance)
        max_items: Limit to top N items by sales volume

    Returns:
        List of sequences; each sequence is a list of frozensets.
        Example: [{101}, {101, 205}, {88}]
    """
    df = sales_df.copy()

    # Limit to top items
    top_items = (
        df.groupby("item_id")["item_cnt_day"]
        .sum()
        .nlargest(max_items)
        .index.tolist()
    )
    df = df[df["item_id"].isin(top_items)]

    # Use first N shops
    shops = df["shop_id"].unique()[:n_shops]
    df = df[df["shop_id"].isin(shops)]

    sequences = []
    for shop_id, shop_df in df.groupby("shop_id"):
        # Order by month
        shop_df = shop_df.sort_values("date_block_num")
        seq = []
        for _, month_df in shop_df.groupby("date_block_num"):
            itemset = frozenset(month_df["item_id"].unique())
            seq.append(itemset)
        if len(seq) >= 2:  # only include shops with at least 2 months
            sequences.append(seq)

    print(f"[preprocessing] Built {len(sequences)} sequences")
    return sequences


# ── 6. Top selling items summary ──────────────────────────────────────────────
def get_top_items(sales_df: pd.DataFrame, items_df: pd.DataFrame, n: int = 10) -> list:
    """
    Return the top N items by total units sold, with item names.
    """
    top = (
        sales_df.groupby("item_id")["item_cnt_day"]
        .sum()
        .nlargest(n)
        .reset_index()
    )
    top.columns = ["item_id", "total_sold"]
    top = top.merge(items_df[["item_id", "item_name"]], on="item_id", how="left")
    return top.to_dict(orient="records")
