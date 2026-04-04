"""
seed_db.py — Populate the SQLite database from CSV files.

Run this ONCE after setting up the project:
    cd backend
    python seed_db.py

It reads items.csv, item_categories.csv, shops.csv, and sales_train.csv,
then inserts them into the database in batches.
"""
import os
import sys
import pandas as pd

# Allow imports from parent (backend/) directory
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, Shop, ItemCategory, Item, Sale

BATCH_SIZE = 5000  # rows inserted per commit


def seed():
    app = create_app()
    with app.app_context():
        # Drop and recreate all tables
        print("[seed] Dropping existing tables …")
        db.drop_all()
        db.create_all()
        print("[seed] Tables created.")

        data_dir = os.path.join(os.path.dirname(__file__), "data")

        # ── 1. Shops ──────────────────────────────────────────────────────────
        shops_path = os.path.join(data_dir, "shops.csv")
        if os.path.exists(shops_path):
            shops_df = pd.read_csv(shops_path, encoding='utf-8')
            for _, row in shops_df.iterrows():
                db.session.add(Shop(id=int(row["shop_id"]), name=row["shop_name"]))
            db.session.commit()
            print(f"[seed] Inserted {len(shops_df)} shops.")

        # ── 2. Item categories ────────────────────────────────────────────────
        cats_path = os.path.join(data_dir, "item_categories.csv")
        if os.path.exists(cats_path):
            cats_df = pd.read_csv(cats_path, encoding='utf-8')
            for _, row in cats_df.iterrows():
                db.session.add(
                    ItemCategory(id=int(row["item_category_id"]), name=row["item_category_name"])
                )
            db.session.commit()
            print(f"[seed] Inserted {len(cats_df)} categories.")

        # ── 3. Items ──────────────────────────────────────────────────────────
        items_path = os.path.join(data_dir, "items.csv")
        sales_path = os.path.join(data_dir, "sales_train.csv")

        if os.path.exists(items_path):
            items_df = pd.read_csv(items_path, encoding='utf-8')
            # Compute avg_price and total_sold from sales if available
            stats = {}
            if os.path.exists(sales_path):
                sales_df = pd.read_csv(sales_path, encoding='utf-8')
                sales_df = sales_df[sales_df["item_cnt_day"] > 0]
                sales_df = sales_df[sales_df["item_price"] > 0]
                stats = (
                    sales_df.groupby("item_id")
                    .agg(avg_price=("item_price", "mean"), total_sold=("item_cnt_day", "sum"))
                    .to_dict(orient="index")
                )

            for _, row in items_df.iterrows():
                iid = int(row["item_id"])
                item_stats = stats.get(iid, {})
                db.session.add(
                    Item(
                        id=iid,
                        name=row["item_name"],
                        category_id=int(row["item_category_id"]),
                        avg_price=item_stats.get("avg_price", 0.0),
                        total_sold=int(item_stats.get("total_sold", 0)),
                    )
                )
            db.session.commit()
            print(f"[seed] Inserted {len(items_df)} items.")

        # ── 4. Sales (largest table — batch insert) ───────────────────────────
        if os.path.exists(sales_path):
            sales_df = pd.read_csv(sales_path, encoding='utf-8')
            total = len(sales_df)
            print(f"[seed] Inserting {total} sales rows in batches of {BATCH_SIZE} …")
            for i in range(0, total, BATCH_SIZE):
                chunk = sales_df.iloc[i : i + BATCH_SIZE]
                for _, row in chunk.iterrows():
                    db.session.add(
                        Sale(
                            date=str(row["date"]),
                            date_block_num=int(row["date_block_num"]),
                            shop_id=int(row["shop_id"]),
                            item_id=int(row["item_id"]),
                            item_price=float(row["item_price"]),
                            item_cnt_day=float(row["item_cnt_day"]),
                        )
                    )
                db.session.commit()
                print(f"[seed]   … committed {min(i + BATCH_SIZE, total)}/{total}")

            print("[seed] Sales inserted.")

        print("[seed] ✅ Database seeded successfully!")


if __name__ == "__main__":
    seed()
