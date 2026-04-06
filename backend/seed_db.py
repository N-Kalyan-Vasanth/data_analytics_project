"""
seed_db.py — Populate the SQLite database from the Online Retail dataset.

Run this ONCE after setting up the project:
    cd backend
    python seed_db.py
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, Shop, ItemCategory, Item, Sale
from ml.preprocessing import load_raw_data, clean_sales

BATCH_SIZE = 5000

def seed():
    app = create_app()
    with app.app_context():
        print("[seed] Dropping existing tables …")
        db.drop_all()
        db.create_all()
        print("[seed] Tables created.")

        print("[seed] Loading dataset from online_retail.csv ...")
        # Load and clean the data
        data = load_raw_data()
        df = clean_sales(data['sales'])

        # We need a fallback date_block_num since the app expects an integer month sequence
        df['date_block_num'] = (df['date'].dt.year - df['date'].dt.year.min()) * 12 + df['date'].dt.month

        # ── 1. Determine unique shops (customers) ─────────────────────────
        unique_shops = df['shop_id'].dropna().unique()
        for s in unique_shops:
            db.session.add(Shop(id=str(s), name=f"Customer {s}"))
        db.session.commit()
        print(f"[seed] Inserted {len(unique_shops)} shops (customers).")

        # ── 2. Create a generic Item Category ──────────────────────────────
        generic_cat = ItemCategory(id=1, name="General Merchandise")
        db.session.add(generic_cat)
        db.session.commit()
        print("[seed] Inserted 'General Merchandise' category.")

        # ── 3. Determine unique Items ──────────────────────────────────────
        item_stats = df.groupby(["item_id"]).agg(
            item_name=("item_name", "first"),
            avg_price=("item_price", "mean"),
            total_sold=("item_cnt_day", "sum")
        ).reset_index()

        for _, row in item_stats.iterrows():
            db.session.add(
                Item(
                    id=str(row["item_id"]),
                    name=str(row["item_name"]),
                    category_id=1, # generic
                    avg_price=float(row["avg_price"]),
                    total_sold=int(row["total_sold"])
                )
            )
        db.session.commit()
        print(f"[seed] Inserted {len(item_stats)} items.")

        # ── 4. Insert Sales ────────────────────────────────────────────────
        total = len(df)
        print(f"[seed] Inserting {total} sales rows in batches of {BATCH_SIZE} …")
        for i in range(0, total, BATCH_SIZE):
            chunk = df.iloc[i : i + BATCH_SIZE]
            for _, row in chunk.iterrows():
                db.session.add(
                    Sale(
                        date=row["date"].strftime("%Y-%m-%d"),
                        date_block_num=int(row["date_block_num"]),
                        shop_id=str(row["shop_id"]),
                        item_id=str(row["item_id"]),
                        item_price=float(row["item_price"]),
                        item_cnt_day=float(row["item_cnt_day"]),
                    )
                )
            db.session.commit()
            print(f"[seed]   … committed {min(i + BATCH_SIZE, total)}/{total}")

        print("[seed] ✅ Database seeded successfully!")

if __name__ == "__main__":
    seed()
