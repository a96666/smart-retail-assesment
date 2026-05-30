"""
Unit tests for REST API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ingest_valid(client: AsyncClient):
    payload = {
        "records": [
            {
                "product_id": "P001",
                "product_name": "Wireless Headphones",
                "category": "Electronics",
                "quantity": 20,
                "unit_price": 49.99,
                "sale_date": "2024-06-01",
                "store_id": "S001",
            }
        ]
    }
    res = await client.post("/api/ingest", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["inserted"] == 1


@pytest.mark.asyncio
async def test_ingest_invalid_date(client: AsyncClient):
    payload = {
        "records": [
            {
                "product_id": "P001",
                "product_name": "Test",
                "category": "Test",
                "quantity": 5,
                "unit_price": 9.99,
                "sale_date": "not-a-date",
                "store_id": "S001",
            }
        ]
    }
    res = await client.post("/api/ingest", json=payload)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_predict(client: AsyncClient):
    res = await client.get("/api/predict?product_id=P001&days=7")
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "P001"
    assert data["forecast_days"] == 7
    assert len(data["forecast"]) == 7
    for point in data["forecast"]:
        assert "date" in point
        assert "predicted_demand" in point
        assert point["predicted_demand"] >= 0


@pytest.mark.asyncio
async def test_predict_invalid_days(client: AsyncClient):
    res = await client.get("/api/predict?product_id=P001&days=100")
    assert res.status_code == 422  # Validation error (max 30)


@pytest.mark.asyncio
async def test_search(client: AsyncClient):
    res = await client.get("/api/search?q=return+policy&k=3")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_agent_qa(client: AsyncClient):
    payload = {"message": "What is the return policy?"}
    res = await client.post("/api/agent", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["response"]) > 0
    assert "session_id" in data
    assert "agent" in data


@pytest.mark.asyncio
async def test_agent_demand(client: AsyncClient):
    payload = {"message": "What is the demand forecast for P001?"}
    res = await client.post("/api/agent", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "demand"


@pytest.mark.asyncio
async def test_anomaly_detection(client: AsyncClient):
    records = [
        {"product_id": "P001", "date": "2024-06-01", "quantity": qty}
        for qty in [20, 25, 18, 22, 300, 19, 21, 24, 17, 23]
    ]
    res = await client.post("/api/anomaly", json={"records": records})
    assert res.status_code == 200
    data = res.json()
    assert "anomaly_count" in data
    assert "total_records" in data
    assert data["total_records"] == 10
    assert "insight" in data


@pytest.mark.asyncio
async def test_anomaly_alerts(client: AsyncClient):
    res = await client.get("/api/anomaly/alerts")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_dashboard(client: AsyncClient):
    res = await client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_revenue_30d" in data
    assert "total_transactions_30d" in data
    assert "anomaly_count_7d" in data
    assert "top_products" in data
    assert "daily_revenue_trend" in data
