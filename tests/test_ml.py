"""
Unit tests for ML models (forecaster + anomaly detector).
"""
import pytest
from app.ml.forecaster import predict_demand, _moving_average_forecast
from app.ml.anomaly_detector import detect_anomalies, _zscore_anomaly
import numpy as np


# ── Forecaster tests ─────────────────────────────────────────────

def test_moving_average_forecast_length():
    history = [10.0, 20.0, 15.0, 18.0, 22.0]
    result = _moving_average_forecast(history, steps=7)
    assert len(result) == 7


def test_moving_average_forecast_non_negative():
    history = [5.0, 3.0, 4.0]
    result = _moving_average_forecast(history, steps=5)
    assert all(v >= 0 for v in result)


def test_predict_demand_returns_correct_length():
    history = [{"date": f"2024-06-{i+1:02d}", "quantity": 20 + i} for i in range(30)]
    result = predict_demand("P001", history, forecast_days=7)
    assert len(result) == 7


def test_predict_demand_structure():
    result = predict_demand("P001", [], forecast_days=3)
    assert len(result) == 3
    for point in result:
        assert "date" in point
        assert "predicted_demand" in point
        assert "lower" in point
        assert "upper" in point
        assert point["predicted_demand"] >= 0
        assert point["lower"] <= point["predicted_demand"]
        assert point["upper"] >= point["predicted_demand"]


def test_predict_demand_empty_history():
    """Should not crash with empty history."""
    result = predict_demand("P999", [], forecast_days=5)
    assert len(result) == 5


# ── Anomaly detector tests ───────────────────────────────────────

def test_zscore_anomaly_detects_spike():
    quantities = np.array([[10], [12], [11], [9], [13], [200], [10], [11]])
    scores, is_anomaly = _zscore_anomaly(quantities, threshold=2.5)
    # The 200 spike should be flagged
    assert is_anomaly[5] == True


def test_zscore_anomaly_normal_data():
    quantities = np.array([[10], [11], [10], [12], [11], [10], [11]])
    scores, is_anomaly = _zscore_anomaly(quantities, threshold=2.5)
    assert sum(is_anomaly) == 0


def test_detect_anomalies_returns_all_records():
    records = [
        {"product_id": "P001", "date": "2024-06-01", "quantity": qty}
        for qty in [20, 25, 18, 300, 22, 19]
    ]
    result = detect_anomalies(records)
    assert len(result) == len(records)


def test_detect_anomalies_fields():
    records = [{"product_id": "P001", "date": "2024-06-01", "quantity": 20}]
    result = detect_anomalies(records)
    assert "is_anomaly" in result[0]
    assert "anomaly_score" in result[0]
    assert "description" in result[0]


def test_detect_anomalies_empty():
    result = detect_anomalies([])
    assert result == []
