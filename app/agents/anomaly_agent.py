"""
Anomaly Detection Agent
Interprets anomaly detection results and generates actionable insights.
"""
import logging
from typing import List, Dict, Any

from app.core.config import settings
from app.ml.anomaly_detector import detect_anomalies

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Retail Analytics Expert specializing in anomaly detection.
You analyze sales anomalies and provide:
- Clear explanation of what the anomaly means
- Possible root causes (stockout, promotion spike, data error, theft, etc.)
- Recommended actions for the operations team
Be concise and prioritize by severity.
"""


def _mock_llm_response(anomalies: List[Dict], context: str) -> str:
    """Rule-based fallback."""
    if not anomalies:
        return "No anomalies detected in the provided sales data. All metrics are within normal ranges."

    high_count = sum(1 for a in anomalies if a.get("anomaly_score", 0) < -2.0)
    total = len(anomalies)

    response = f"Anomaly Analysis Summary:\n"
    response += f"- Total anomalies detected: {total}\n"
    response += f"- High severity: {high_count}\n\n"

    for a in anomalies[:5]:  # Show top 5
        response += (
            f"• Product {a.get('product_id', 'N/A')} on {a.get('date', 'N/A')}: "
            f"Quantity={a.get('quantity', 'N/A')}, Score={a.get('anomaly_score', 0):.3f}\n"
            f"  → Possible cause: {'Demand spike – check promotions or external events' if a.get('quantity', 0) > 100 else 'Unusual drop – check stockout or data quality'}\n"
        )

    response += "\nRecommended Actions:\n"
    response += "1. Verify data quality for flagged records\n"
    response += "2. Cross-check with promotion calendar\n"
    response += "3. Alert inventory team for potential stockout risks\n"
    return response


def _azure_llm_response(anomalies: List[Dict], context: str) -> str:
    """Call Azure OpenAI for anomaly interpretation."""
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Anomaly data:\n{context}\n\nProvide analysis and recommendations."},
        ]
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=messages,
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("Azure OpenAI call failed: %s", exc)
        return _mock_llm_response(anomalies, context)


class AnomalyDetectionAgent:
    """Agent that detects and interprets sales anomalies."""

    name = "AnomalyDetectionAgent"

    def run(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("[AnomalyDetectionAgent] Analyzing %d records", len(records))

        results = detect_anomalies(records)
        anomalies = [r for r in results if r.get("is_anomaly")]

        # Build context string for LLM
        context_lines = [f"Total records: {len(records)}", f"Anomalies found: {len(anomalies)}", ""]
        for a in anomalies[:10]:
            context_lines.append(
                f"Product {a.get('product_id')} | Date: {a.get('date')} | "
                f"Qty: {a.get('quantity')} | Score: {a.get('anomaly_score', 0):.3f}"
            )
        context = "\n".join(context_lines)

        if settings.use_azure_openai:
            insight = _azure_llm_response(anomalies, context)
        else:
            insight = _mock_llm_response(anomalies, context)

        return {
            "total_records": len(records),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "insight": insight,
        }
