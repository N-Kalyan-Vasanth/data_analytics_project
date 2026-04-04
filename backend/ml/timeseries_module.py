"""
ml/timeseries_module.py — Time Series Forecasting (ARIMA + Moving Average).

Aggregates daily sales to monthly, fits an ARIMA model, and forecasts
future months. Also provides a simple Moving Average baseline.

Exported functions:
  - run_timeseries(monthly_df, arima_order, forecast_months) → dict
  - run_moving_average(monthly_df, window, forecast_months) → dict
"""
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    print("[timeseries] statsmodels not available — ARIMA disabled")


# ── ARIMA Forecasting ─────────────────────────────────────────────────────────
def run_arima(
    monthly_df: pd.DataFrame,
    arima_order: tuple = (1, 1, 1),
    forecast_months: int = 3,
) -> dict:
    """
    Fit an ARIMA model on monthly total_items and forecast future months.

    Args:
        monthly_df:     DataFrame with columns [year_month_str, total_items]
        arima_order:    (p, d, q) ARIMA hyperparameters
        forecast_months: Number of months to predict beyond the last data point

    Returns:
        {
          'historical':  [{'month': str, 'actual': float}],
          'forecast':    [{'month': str, 'predicted': float}],
          'model':       'ARIMA',
          'order':       [p, d, q],
          'metrics': {'aic': float, 'bic': float},
        }
    """
    if not ARIMA_AVAILABLE:
        return {"error": "statsmodels not installed", "model": "ARIMA"}

    series = monthly_df["total_items"].values.astype(float)
    months = monthly_df["year_month_str"].tolist()

    # Fit ARIMA
    try:
        model = ARIMA(series, order=arima_order)
        fitted = model.fit()
    except Exception as e:
        return {"error": str(e), "model": "ARIMA"}

    # In-sample fitted values
    fitted_vals = fitted.fittedvalues.tolist()

    # Out-of-sample forecast
    forecast_result = fitted.forecast(steps=forecast_months)
    forecast_vals = forecast_result.tolist()

    # Generate future month labels
    last_period = pd.Period(months[-1], freq="M")
    future_months = [
        str(last_period + i + 1) for i in range(forecast_months)
    ]

    return {
        "historical": [
            {"month": m, "actual": round(v, 2), "fitted": round(f, 2)}
            for m, v, f in zip(months, series.tolist(), fitted_vals)
        ],
        "forecast": [
            {"month": m, "predicted": round(max(v, 0), 2)}
            for m, v in zip(future_months, forecast_vals)
        ],
        "model": "ARIMA",
        "order": list(arima_order),
        "metrics": {
            "aic": round(fitted.aic, 2),
            "bic": round(fitted.bic, 2),
        },
    }


# ── Moving Average Baseline ───────────────────────────────────────────────────
def run_moving_average(
    monthly_df: pd.DataFrame,
    window: int = 3,
    forecast_months: int = 3,
) -> dict:
    """
    Simple rolling moving average forecast.

    The forecast for each future month is the mean of the last `window` months.

    Args:
        monthly_df:     DataFrame with [year_month_str, total_items]
        window:         Rolling window size (default 3 months)
        forecast_months: Months to forecast

    Returns:
        {
          'historical':  [{'month': str, 'actual': float, 'smoothed': float}],
          'forecast':    [{'month': str, 'predicted': float}],
          'model':       'MovingAverage',
          'window':      int,
        }
    """
    df = monthly_df.copy()
    series = df["total_items"].values.astype(float)
    months = df["year_month_str"].tolist()

    # Rolling mean (NaN for first window-1 values)
    smoothed = pd.Series(series).rolling(window=window, min_periods=1).mean().tolist()

    # Forecast: use mean of last `window` real values
    last_vals = series[-window:]
    predicted_val = float(np.mean(last_vals))

    last_period = pd.Period(months[-1], freq="M")
    future_months = [str(last_period + i + 1) for i in range(forecast_months)]

    return {
        "historical": [
            {"month": m, "actual": round(v, 2), "smoothed": round(s, 2)}
            for m, v, s in zip(months, series.tolist(), smoothed)
        ],
        "forecast": [
            {"month": m, "predicted": round(predicted_val, 2)}
            for m in future_months
        ],
        "model": "MovingAverage",
        "window": window,
    }


# ── Unified entry point ───────────────────────────────────────────────────────
def run_timeseries(
    monthly_df: pd.DataFrame,
    arima_order: tuple = (1, 1, 1),
    ma_window: int = 3,
    forecast_months: int = 3,
) -> dict:
    """
    Run both ARIMA and Moving Average and return results together.

    Args:
        monthly_df:      Aggregated monthly DataFrame
        arima_order:     ARIMA (p,d,q) params
        ma_window:       Moving average window
        forecast_months: How many months ahead to forecast

    Returns:
        {'arima': {...}, 'moving_average': {...}}
    """
    arima_result = run_arima(monthly_df, arima_order, forecast_months)
    ma_result = run_moving_average(monthly_df, ma_window, forecast_months)
    return {"arima": arima_result, "moving_average": ma_result}
