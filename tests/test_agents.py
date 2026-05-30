"""
Unit tests for the agent layer.
"""
import pytest
from app.agents.orchestrator import AgentOrchestrator, _classify_intent
from app.agents.demand_agent import DemandForecastAgent
from app.agents.qa_agent import CustomerQAAgent
from app.agents.anomaly_agent import AnomalyDetectionAgent


# ── Intent classifier ────────────────────────────────────────────

def test_classify_demand_intent():
    assert _classify_intent("What is the demand forecast for P001?") == "demand"
    assert _classify_intent("Show me sales trend for next week") == "demand"
    assert _classify_intent("How much stock should I reorder?") == "demand"


def test_classify_anomaly_intent():
    assert _classify_intent("Are there any anomalies in sales?") == "anomaly"
    assert _classify_intent("Detect unusual patterns in data") == "anomaly"


def test_classify_qa_intent():
    assert _classify_intent("What is the return policy?") == "qa"
    assert _classify_intent("What are your store hours?") == "qa"
    assert _classify_intent("How do I contact support?") == "qa"


# ── Demand Agent ─────────────────────────────────────────────────

def test_demand_agent_returns_string():
    agent = DemandForecastAgent()
    result = agent.run("What is the forecast for P001?", product_id="P001")
    assert isinstance(result, str)
    assert len(result) > 0


def test_demand_agent_with_history():
    agent = DemandForecastAgent()
    history = [{"date": f"2024-06-{i+1:02d}", "quantity": 20 + i} for i in range(14)]
    result = agent.run("Forecast demand", product_id="P001", history=history)
    assert isinstance(result, str)


# ── Customer Q&A Agent ───────────────────────────────────────────

def test_qa_agent_return_policy():
    agent = CustomerQAAgent()
    result = agent.run("What is the return policy?")
    assert isinstance(result, str)
    assert len(result) > 0


def test_qa_agent_store_hours():
    agent = CustomerQAAgent()
    result = agent.run("What are your opening hours?")
    assert isinstance(result, str)


# ── Anomaly Agent ────────────────────────────────────────────────

def test_anomaly_agent_no_anomalies():
    agent = AnomalyDetectionAgent()
    records = [
        {"product_id": "P001", "date": f"2024-06-{i+1:02d}", "quantity": 20 + i % 5}
        for i in range(20)
    ]
    result = agent.run(records)
    assert "total_records" in result
    assert result["total_records"] == 20
    assert "insight" in result
    assert isinstance(result["insight"], str)


def test_anomaly_agent_with_spike():
    agent = AnomalyDetectionAgent()
    records = [
        {"product_id": "P001", "date": "2024-06-01", "quantity": qty}
        for qty in [20, 22, 19, 21, 500, 18, 23, 20, 21, 19]
    ]
    result = agent.run(records)
    assert result["anomaly_count"] >= 1


# ── Orchestrator ─────────────────────────────────────────────────

def test_orchestrator_routes_to_qa():
    orch = AgentOrchestrator()
    result = orch.run("What is the return policy?")
    assert result["agent"] == "CustomerQAAgent"
    assert result["intent"] == "qa"
    assert len(result["response"]) > 0


def test_orchestrator_routes_to_demand():
    orch = AgentOrchestrator()
    result = orch.run("What is the demand forecast for P001?", context={"product_id": "P001"})
    assert result["agent"] == "DemandForecastAgent"
    assert result["intent"] == "demand"


def test_orchestrator_routes_to_anomaly_no_records():
    orch = AgentOrchestrator()
    result = orch.run("Are there any anomalies?")
    assert result["agent"] == "AnomalyDetectionAgent"
    assert result["intent"] == "anomaly"
    # Should return a helpful message, not crash
    assert len(result["response"]) > 0


def test_orchestrator_routes_to_anomaly_with_records():
    orch = AgentOrchestrator()
    records = [
        {"product_id": "P001", "date": f"2024-06-{i+1:02d}", "quantity": 20 + i % 5}
        for i in range(10)
    ]
    result = orch.run("Detect anomalies", context={"records": records})
    assert result["intent"] == "anomaly"
    assert "data" in result
