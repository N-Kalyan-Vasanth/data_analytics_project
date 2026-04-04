"""
app.py — Flask application factory and entry point.

Usage:
    cd backend
    python app.py          # development server on :5000
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from config import Config
from routes.products import products_bp
from routes.cart import cart_bp
from routes.recommendations import recs_bp
from routes.predictions import predictions_bp
from routes.patterns import patterns_bp


def create_app(config_class=Config):
    """
    Application factory — creates and configures the Flask app.
    Using a factory lets us create separate instances for testing.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Secret key for session cookies (cart)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # ── CORS — allow requests from the React dev server ──────────────────────
    CORS(
        app,
        origins=config_class.CORS_ORIGINS,
        supports_credentials=True,
    )

    # ── Database ─────────────────────────────────────────────────────────────
    db.init_app(app)
    with app.app_context():
        os.makedirs(os.path.join(os.path.dirname(__file__), "db"), exist_ok=True)
        db.create_all()  # creates tables if they don't exist

    # ── Register blueprints ───────────────────────────────────────────────────
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(recs_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(patterns_bp)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "DataMine E-Commerce API is running"})

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found", "message": str(e)}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Server error", "message": str(e)}), 500

    return app


# ── Run dev server ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("  DataMine E-Commerce API")
    print("  http://localhost:5000/api/health")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
