"""
Multi-Agent Orchestrator
Routes user queries to the appropriate agent based on intent classification.
"""
import logging
from typing import Dict, Any

from app.agents.demand_agent import DemandForecastAgent
from app.agents.qa_agent import CustomerQAAgent
from app.agents.anomaly_agent import AnomalyDetectionAgent

logger = logging.getLogger(__name__)

# Intent keywords for routing
DEMAND_KEYWORDS = [
    "forecast", "demand", "predict", "trend", "inventory",
    "stock", "reorder", "supply", "units", "quantity next",
    "sales forecast", "sales trend", "sales prediction",
]
ANOMALY_KEYWORDS = [
    "anomaly", "anomalies", "unusual", "spike", "drop", "alert",
    "outlier", "abnormal", "suspicious", "detect",
    "strange", "weird", "unexpected", "irregular",
]


def _classify_intent(message: str) -> str:
    """Simple keyword-based intent classifier.

    Anomaly intent wins on a tie because anomaly keywords are more
    specific than demand keywords (e.g. 'sales' was removed from demand
    to avoid false matches like 'anomalies in sales').
    """
    msg = message.lower()
    demand_score = sum(1 for kw in DEMAND_KEYWORDS if kw in msg)
    anomaly_score = sum(1 for kw in ANOMALY_KEYWORDS if kw in msg)

    # Anomaly wins on tie – anomaly keywords are more specific
    if anomaly_score >= demand_score and anomaly_score > 0:
        return "anomaly"
    if demand_score > 0:
        return "demand"
    return "qa"  # default to customer Q&A


class AgentOrchestrator:
    """Routes queries to the right agent and returns structured responses."""

    def __init__(self):
        self.demand_agent = DemandForecastAgent()
        self.qa_agent = CustomerQAAgent()
        self.anomaly_agent = AnomalyDetectionAgent()

    def run(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route message to the appropriate agent.

        Args:
            message: User's natural language query.
            context: Optional extra context (product_id, records, etc.)

        Returns:
            Dict with 'agent', 'response', and optional 'data'.
        """
        context = context or {}
        intent = _classify_intent(message)
        logger.info("Orchestrator: intent=%s | message=%s", intent, message)

        try:
            if intent == "demand":
                product_id = context.get("product_id", "P001")
                history = context.get("history", [])
                response = self.demand_agent.run(message, product_id=product_id, history=history)
                return {"agent": self.demand_agent.name, "intent": intent, "response": response}

            elif intent == "anomaly":
                records = context.get("records", [])
                if not records:
                    # Return a helpful message if no records provided
                    return {
                        "agent": self.anomaly_agent.name,
                        "intent": intent,
                        "response": (
                            "To run anomaly detection, please provide sales records via "
                            "the /api/anomaly endpoint or include 'records' in your request context."
                        ),
                    }
                result = self.anomaly_agent.run(records)
                return {
                    "agent": self.anomaly_agent.name,
                    "intent": intent,
                    "response": result["insight"],
                    "data": {
                        "anomaly_count": result["anomaly_count"],
                        "total_records": result["total_records"],
                    },
                }

            else:  # qa
                response = self.qa_agent.run(message)
                return {"agent": self.qa_agent.name, "intent": intent, "response": response}

        except Exception as exc:
            logger.error("Orchestrator error: %s", exc, exc_info=True)
            return {
                "agent": "Orchestrator",
                "intent": intent,
                "response": f"An error occurred while processing your request: {str(exc)}",
            }
