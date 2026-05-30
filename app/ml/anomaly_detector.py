"""
Anomaly Detection – Isolation Forest model for sales anomalies.
Falls back to z-score method if no model file is found.
"""
import logging
import os
from typing import List, Dict, Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join("ml_models", "anomaly_model.pkl")


def load_model():
    if os.path.exists(MODEL_PATH):
        logger.info("Loading anomaly model from %s", MODEL_PATH)
        return joblib.load(MODEL_PATH)
    logger.warning("No anomaly model found – using z-score fallback")
    return None


def detect_anomalies(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect anomalies in sales records.

    Args:
        records: List of dicts with 'product_id', 'date', 'quantity'.

    Returns:
        Same records enriched with 'is_anomaly', 'anomaly_score', 'description'.
    """
    if not records:
        return []

    quantities = np.array([float(r["quantity"]) for r in records]).reshape(-1, 1)
    model = load_model()

    if model is not None:
        try:
            scores = model.decision_function(quantities)   # higher = more normal
            labels = model.predict(quantities)             # -1 = anomaly, 1 = normal
            is_anomaly = labels == -1
        except Exception as exc:
            logger.error("Anomaly model failed: %s – using z-score", exc)
            scores, is_anomaly = _zscore_anomaly(quantities)
    else:
        scores, is_anomaly = _zscore_anomaly(quantities)

    results = []
    for i, record in enumerate(records):
        anomaly = bool(is_anomaly[i])
        score = float(scores[i])
        description = (
            f"Unusual sales volume detected for {record.get('product_id', 'unknown')} "
            f"on {record.get('date', 'unknown')} (score: {score:.3f})"
            if anomaly else ""
        )
        results.append({
            **record,
            "is_anomaly": anomaly,
            "anomaly_score": round(score, 4),
            "description": description,
        })

    anomaly_count = sum(1 for r in results if r["is_anomaly"])
    logger.info("Anomaly detection complete: %d/%d flagged", anomaly_count, len(results))
    return results


def _zscore_anomaly(quantities: np.ndarray, threshold: float = 2.5):
    """Z-score based anomaly detection fallback."""
    mean = np.mean(quantities)
    std = np.std(quantities) + 1e-9
    z_scores = np.abs((quantities - mean) / std).flatten()
    is_anomaly = z_scores > threshold
    # Invert so higher score = more anomalous (consistent with IF convention)
    scores = -z_scores
    return scores, is_anomaly
