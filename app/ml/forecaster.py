"""
Demand Forecasting – loads the trained model and runs predictions.
Falls back to a simple moving-average if no model file is found.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join("ml_models", "demand_model.pkl")


def _moving_average_forecast(history: List[float], steps: int = 7) -> List[float]:
    """Simple fallback: 7-day moving average."""
    window = min(7, len(history))
    avg = float(np.mean(history[-window:]))
    noise = np.random.normal(0, avg * 0.05, steps)
    return [max(0.0, avg + n) for n in noise]


def load_model():
    if os.path.exists(MODEL_PATH):
        logger.info("Loading demand model from %s", MODEL_PATH)
        return joblib.load(MODEL_PATH)
    logger.warning("No model file found at %s – using moving average fallback", MODEL_PATH)
    return None


def predict_demand(
    product_id: str,
    history: List[Dict[str, Any]],
    forecast_days: int = 7,
) -> List[Dict[str, Any]]:
    """
    Predict demand for the next `forecast_days` days.

    Args:
        product_id: Product identifier.
        history: List of dicts with keys 'date' and 'quantity'.
        forecast_days: Number of days to forecast.

    Returns:
        List of dicts with 'date', 'predicted_demand', 'lower', 'upper'.
    """
    model = load_model()

    quantities = [float(r["quantity"]) for r in history] if history else [50.0] * 30

    if model is not None:
        try:
            # Build feature matrix: lag features
            df = pd.DataFrame({"qty": quantities})
            for lag in [1, 2, 3, 7]:
                df[f"lag_{lag}"] = df["qty"].shift(lag)
            df = df.dropna()

            if len(df) == 0:
                preds = _moving_average_forecast(quantities, forecast_days)
            else:
                last_row = df.iloc[-1][["lag_1", "lag_2", "lag_3", "lag_7"]].values
                preds = []
                row = last_row.copy()
                for _ in range(forecast_days):
                    pred = float(model.predict(row.reshape(1, -1))[0])
                    pred = max(0.0, pred)
                    preds.append(pred)
                    row = np.roll(row, 1)
                    row[0] = pred
        except Exception as exc:
            logger.error("Model prediction failed: %s – falling back", exc)
            preds = _moving_average_forecast(quantities, forecast_days)
    else:
        preds = _moving_average_forecast(quantities, forecast_days)

    std = float(np.std(quantities)) if quantities else 5.0
    base_date = datetime.utcnow().date()

    results = []
    for i, pred in enumerate(preds):
        results.append({
            "date": str(base_date + timedelta(days=i + 1)),
            "predicted_demand": round(pred, 2),
            "lower": round(max(0.0, pred - 1.96 * std), 2),
            "upper": round(pred + 1.96 * std, 2),
        })

    logger.info("Forecast generated for product %s (%d days)", product_id, forecast_days)
    return results
