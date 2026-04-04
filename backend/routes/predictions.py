"""
routes/predictions.py — Time series forecasting API.

Endpoints:
  GET /api/predictions/monthly       → historical monthly sales + ARIMA forecast
  GET /api/predictions/moving-avg    → Moving Average forecast
  GET /api/predictions/summary       → KPI summary (totals, growth)
  GET /api/predictions/by-item/<id>  → monthly sales trend for one item
"""
from flask import Blueprint, jsonify, request, current_app
from models import db, Sale, Item
from ml.preprocessing import load_raw_data, get_cached_cleaned_sales, aggregate_monthly, aggregate_monthly_by_item
from ml.timeseries_module import run_timeseries, run_arima, run_moving_average
import pandas as pd

predictions_bp = Blueprint("predictions", __name__)

# In-memory cache
_ts_cache = None
_monthly_cache = None


def _get_monthly_df():
    global _monthly_cache
    if _monthly_cache is not None:
        return _monthly_cache

    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        return pd.DataFrame()
    _monthly_cache = aggregate_monthly(cleaned)
    return _monthly_cache


# ── GET /api/predictions/monthly ──────────────────────────────────────────────
@predictions_bp.route("/api/predictions/monthly", methods=["GET"])
def get_monthly_predictions():
    """
    Returns historical monthly sales data + ARIMA forecast.
    Query params:
      - p, d, q: ARIMA order (default 1,1,1)
      - months: forecast horizon (default 3)
    """
    p = request.args.get("p", 1, type=int)
    d = request.args.get("d", 1, type=int)
    q = request.args.get("q", 1, type=int)
    forecast_months = request.args.get("months", 3, type=int)

    monthly_df = _get_monthly_df()
    if monthly_df.empty:
        return jsonify({"error": "No sales data available"}), 500

    result = run_arima(monthly_df, arima_order=(p, d, q), forecast_months=forecast_months)
    return jsonify(result)


# ── GET /api/predictions/moving-avg ───────────────────────────────────────────
@predictions_bp.route("/api/predictions/moving-avg", methods=["GET"])
def get_ma_predictions():
    """
    Returns Moving Average smoothed historical + forecast.
    Query params:
      - window: rolling window (default 3)
      - months: forecast horizon (default 3)
    """
    window = request.args.get("window", 3, type=int)
    forecast_months = request.args.get("months", 3, type=int)

    monthly_df = _get_monthly_df()
    if monthly_df.empty:
        return jsonify({"error": "No sales data available"}), 500

    result = run_moving_average(monthly_df, window=window, forecast_months=forecast_months)
    return jsonify(result)


# ── GET /api/predictions/summary ──────────────────────────────────────────────
@predictions_bp.route("/api/predictions/summary", methods=["GET"])
def get_summary():
    """
    Returns high-level KPIs:
      - total items sold
      - total revenue
      - peak month
      - avg monthly sales
      - growth rate (last month vs. previous month)
    """
    monthly_df = _get_monthly_df()
    if monthly_df.empty:
        return jsonify({"error": "No data"}), 500

    total_items = int(monthly_df["total_items"].sum())
    total_revenue = float(monthly_df["total_revenue"].sum())
    peak_idx = monthly_df["total_items"].idxmax()
    peak_month = monthly_df.loc[peak_idx, "year_month_str"]
    avg_monthly = float(monthly_df["total_items"].mean())

    last_two = monthly_df.tail(2)["total_items"].values
    if len(last_two) == 2 and last_two[0] > 0:
        growth = float((last_two[1] - last_two[0]) / last_two[0] * 100)
    else:
        growth = 0.0

    return jsonify(
        {
            "total_items_sold": total_items,
            "total_revenue": round(total_revenue, 2),
            "avg_monthly_items": round(avg_monthly, 2),
            "peak_month": peak_month,
            "growth_rate_pct": round(growth, 2),
            "data_months": len(monthly_df),
        }
    )


# ── GET /api/predictions/by-item/<item_id> ────────────────────────────────────
@predictions_bp.route("/api/predictions/by-item/<int:item_id>", methods=["GET"])
def get_item_prediction(item_id):
    """Return monthly sales history for a specific item."""
    cleaned = get_cached_cleaned_sales()
    if cleaned.empty:
        return jsonify({"error": "No data"}), 500
    item_df = cleaned[cleaned["item_id"] == item_id]

    if item_df.empty:
        return jsonify({"error": f"No sales found for item {item_id}"}), 404

    y = 2013 + (item_df["date_block_num"] // 12)
    m = (item_df["date_block_num"] % 12) + 1
    item_df["year_month_str"] = y.astype(str) + "-" + m.astype(str).str.zfill(2)

    monthly = (
        item_df.groupby("year_month_str")
        .agg(total_items=("item_cnt_day", "sum"))
        .reset_index()
        .sort_values("year_month_str")
    )

    item = Item.query.get(item_id)
    return jsonify(
        {
            "item_id": item_id,
            "item_name": item.name if item else f"Item {item_id}",
            "monthly_sales": monthly[["year_month_str", "total_items"]].to_dict(orient="records"),
        }
    )


# ── GET /api/predictions/all ───────────────────────────────────────────────────
@predictions_bp.route("/api/predictions/all", methods=["GET"])
def get_all_predictions():
    """Run both ARIMA and Moving Average and return together."""
    monthly_df = _get_monthly_df()
    if monthly_df.empty:
        return jsonify({"error": "No data"}), 500

    result = run_timeseries(
        monthly_df,
        arima_order=tuple(current_app.config.get("ARIMA_ORDER", (1, 1, 1))),
        ma_window=3,
        forecast_months=current_app.config.get("FORECAST_MONTHS", 3),
    )
    return jsonify(result)
