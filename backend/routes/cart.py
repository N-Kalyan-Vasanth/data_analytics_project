"""
routes/cart.py — Shopping cart REST API (session-based).

Endpoints:
  GET    /api/cart              → view cart
  POST   /api/cart              → add item to cart
  PUT    /api/cart/<id>         → update quantity
  DELETE /api/cart/<id>         → remove item
  DELETE /api/cart              → clear cart
"""
import uuid
from flask import Blueprint, jsonify, request, session
from models import db, CartItem, Item

cart_bp = Blueprint("cart", __name__)


def _get_session_id() -> str:
    """Return or create a session ID stored in secure cookie."""
    if "cart_session" not in session:
        session["cart_session"] = str(uuid.uuid4())
    return session["cart_session"]


# ── GET /api/cart ─────────────────────────────────────────────────────────────
@cart_bp.route("/api/cart", methods=["GET"])
def get_cart():
    """Return all items in the current session's cart."""
    sid = _get_session_id()
    items = CartItem.query.filter_by(session_id=sid).all()
    cart_data = [ci.to_dict() for ci in items]
    total = sum(ci["subtotal"] for ci in cart_data)
    return jsonify({"cart": cart_data, "total": round(total, 2), "count": len(cart_data)})


# ── POST /api/cart ────────────────────────────────────────────────────────────
@cart_bp.route("/api/cart", methods=["POST"])
def add_to_cart():
    """
    Add an item to cart or increment quantity if already present.
    Body: { "item_id": int, "quantity": int (optional, default 1) }
    """
    sid = _get_session_id()
    data = request.get_json(force=True)
    item_id = data.get("item_id")
    quantity = max(1, int(data.get("quantity", 1)))

    if not item_id:
        return jsonify({"error": "item_id is required"}), 400

    # Verify item exists
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": f"Item {item_id} not found"}), 404

    # Check if already in cart → increment
    existing = CartItem.query.filter_by(session_id=sid, item_id=item_id).first()
    if existing:
        existing.quantity += quantity
    else:
        db.session.add(CartItem(session_id=sid, item_id=item_id, quantity=quantity))

    db.session.commit()
    return jsonify({"message": "Item added to cart", "item_id": item_id}), 201


# ── PUT /api/cart/<cart_item_id> ──────────────────────────────────────────────
@cart_bp.route("/api/cart/<int:cart_item_id>", methods=["PUT"])
def update_cart_item(cart_item_id):
    """
    Update quantity of a cart item.
    Body: { "quantity": int }
    """
    sid = _get_session_id()
    ci = CartItem.query.filter_by(id=cart_item_id, session_id=sid).first_or_404()
    data = request.get_json(force=True)
    quantity = int(data.get("quantity", 1))

    if quantity <= 0:
        db.session.delete(ci)
    else:
        ci.quantity = quantity

    db.session.commit()
    return jsonify({"message": "Cart updated"})


# ── DELETE /api/cart/<cart_item_id> ───────────────────────────────────────────
@cart_bp.route("/api/cart/<int:cart_item_id>", methods=["DELETE"])
def remove_cart_item(cart_item_id):
    """Remove a specific item from cart."""
    sid = _get_session_id()
    ci = CartItem.query.filter_by(id=cart_item_id, session_id=sid).first_or_404()
    db.session.delete(ci)
    db.session.commit()
    return jsonify({"message": "Item removed from cart"})


# ── DELETE /api/cart ──────────────────────────────────────────────────────────
@cart_bp.route("/api/cart", methods=["DELETE"])
def clear_cart():
    """Remove all items from the current session's cart."""
    sid = _get_session_id()
    CartItem.query.filter_by(session_id=sid).delete()
    db.session.commit()
    return jsonify({"message": "Cart cleared"})
