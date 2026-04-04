"""
routes/products.py — REST API endpoints for products, categories, and shops.

Endpoints:
  GET /api/products              → paginated product list
  GET /api/products/<id>         → single product detail
  GET /api/products/search       → search by name
  GET /api/categories            → all categories
  GET /api/categories/<id>/items → items in a category
  GET /api/shops                 → all shops
  GET /api/top-products          → top selling products
"""
from flask import Blueprint, jsonify, request
from models import db, Item, ItemCategory, Shop
from sqlalchemy.orm import joinedload

products_bp = Blueprint("products", __name__)


# ── GET /api/products ─────────────────────────────────────────────────────────
@products_bp.route("/api/products", methods=["GET"])
def get_products():
    """
    Return a paginated list of products.
    Query params:
      - page (int, default 1)
      - per_page (int, default 20, max 100)
      - category_id (int, optional)
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    category_id = request.args.get("category_id", type=int)

    query = Item.query.options(joinedload(Item.category))
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Sort by total_sold descending so popular items appear first
    query = query.order_by(Item.total_sold.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [item.to_dict() for item in paginated.items],
            "total": paginated.total,
            "page": page,
            "per_page": per_page,
            "pages": paginated.pages,
        }
    )


# ── GET /api/products/search ──────────────────────────────────────────────────
@products_bp.route("/api/products/search", methods=["GET"])
def search_products():
    """
    Search products by name (case-insensitive partial match).
    Query param: q (search string)
    """
    q = request.args.get("q", "", type=str).strip()
    if not q:
        return jsonify({"items": [], "error": "Missing query parameter 'q'"}), 400

    results = (
        Item.query.options(joinedload(Item.category)).filter(Item.name.ilike(f"%{q}%"))
        .order_by(Item.total_sold.desc())
        .limit(30)
        .all()
    )
    return jsonify({"items": [item.to_dict() for item in results], "query": q})


# ── GET /api/products/<id> ────────────────────────────────────────────────────
@products_bp.route("/api/products/<int:item_id>", methods=["GET"])
def get_product(item_id):
    """Return a single product by item_id."""
    item = Item.query.options(joinedload(Item.category)).get_or_404(item_id)
    return jsonify(item.to_dict())


# ── GET /api/categories ───────────────────────────────────────────────────────
@products_bp.route("/api/categories", methods=["GET"])
def get_categories():
    """Return all item categories."""
    cats = ItemCategory.query.order_by(ItemCategory.name).all()
    return jsonify({"categories": [c.to_dict() for c in cats]})


# ── GET /api/categories/<id>/items ───────────────────────────────────────────
@products_bp.route("/api/categories/<int:cat_id>/items", methods=["GET"])
def get_category_items(cat_id):
    """Return all items in a given category, paginated."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    cat = ItemCategory.query.get_or_404(cat_id)
    paginated = (
        Item.query.options(joinedload(Item.category)).filter_by(category_id=cat_id)
        .order_by(Item.total_sold.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify(
        {
            "category": cat.to_dict(),
            "items": [i.to_dict() for i in paginated.items],
            "total": paginated.total,
            "page": page,
            "pages": paginated.pages,
        }
    )


# ── GET /api/shops ────────────────────────────────────────────────────────────
@products_bp.route("/api/shops", methods=["GET"])
def get_shops():
    """Return all shops."""
    shops = Shop.query.order_by(Shop.name).all()
    return jsonify({"shops": [s.to_dict() for s in shops]})


# ── GET /api/top-products ─────────────────────────────────────────────────────
@products_bp.route("/api/top-products", methods=["GET"])
def get_top_products():
    """Return top 10 best-selling products."""
    n = request.args.get("n", 10, type=int)
    items = Item.query.options(joinedload(Item.category)).order_by(Item.total_sold.desc()).limit(n).all()
    return jsonify({"items": [i.to_dict() for i in items]})
