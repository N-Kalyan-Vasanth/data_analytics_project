"""
models.py — SQLAlchemy ORM models for the e-commerce database.

Tables:
  - Shop        → shops from shops.csv
  - ItemCategory → from item_categories.csv
  - Item         → from items.csv (products)
  - Sale         → from sales_train.csv
  - CartItem     → in-session shopping cart (session-based)
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Shop(db.Model):
    """Represents a physical / online shop location."""
    __tablename__ = "shops"

    id = db.Column(db.String(50), primary_key=True)            # shop_id from CSV
    name = db.Column(db.String(255), nullable=False)        # shop_name
    sales = db.relationship("Sale", backref="shop", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self._ensure_utf8(self.name)}

    @staticmethod
    def _ensure_utf8(text):
        """Ensure proper UTF-8 encoding of text from database."""
        if isinstance(text, str):
            return text.encode('utf-8', errors='replace').decode('utf-8')
        return text


class ItemCategory(db.Model):
    """Product categories (e.g. 'PC Games', 'Books')."""
    __tablename__ = "item_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    items = db.relationship("Item", backref="category", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self._ensure_utf8(self.name)}

    @staticmethod
    def _ensure_utf8(text):
        """Ensure proper UTF-8 encoding of text from database."""
        if isinstance(text, str):
            return text.encode('utf-8', errors='replace').decode('utf-8')
        return text


class Item(db.Model):
    """A sellable product/item."""
    __tablename__ = "items"

    id = db.Column(db.String(50), primary_key=True)            # item_id from CSV
    name = db.Column(db.String(512), nullable=False)        # item_name
    category_id = db.Column(db.Integer, db.ForeignKey("item_categories.id"))
    avg_price = db.Column(db.Float, default=0.0)            # computed from sales
    total_sold = db.Column(db.Integer, default=0)           # computed from sales
    sales = db.relationship("Sale", backref="item", lazy=True)

    def to_dict(self, include_category=True):
        data = {
            "id": self.id,
            "name": self._ensure_utf8(self.name),
            "category_id": self.category_id,
            "avg_price": round(self.avg_price, 2),
            "total_sold": self.total_sold,
        }
        if include_category and self.category:
            data["category_name"] = self._ensure_utf8(self.category.name)
        return data

    @staticmethod
    def _ensure_utf8(text):
        """Ensure proper UTF-8 encoding of item names from database."""
        if isinstance(text, str):
            return text.encode('utf-8', errors='replace').decode('utf-8')
        return text


class Sale(db.Model):
    """A single daily sales transaction row from sales_train.csv."""
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(20), nullable=False)         # '02.01.2013'
    date_block_num = db.Column(db.Integer, nullable=False)  # 0-based month index
    shop_id = db.Column(db.String(50), db.ForeignKey("shops.id"))
    item_id = db.Column(db.String(50), db.ForeignKey("items.id"))
    item_price = db.Column(db.Float, nullable=False)
    item_cnt_day = db.Column(db.Float, nullable=False)      # can be negative (refund)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "date_block_num": self.date_block_num,
            "shop_id": self.shop_id,
            "item_id": self.item_id,
            "item_price": self.item_price,
            "item_cnt_day": self.item_cnt_day,
        }


class CartItem(db.Model):
    """Ephemeral shopping cart (session-based)."""
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    item_id = db.Column(db.String(50), db.ForeignKey("items.id"))
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship("Item")

    def to_dict(self):
        return {
            "cart_item_id": self.id,
            "session_id": self.session_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "item_name": self.item.name if self.item else None,
            "unit_price": round(self.item.avg_price, 2) if self.item else 0,
            "subtotal": round(self.quantity * self.item.avg_price, 2) if self.item else 0,
        }
