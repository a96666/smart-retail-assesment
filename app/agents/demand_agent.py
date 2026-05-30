"""
Demand Forecast Agent
Answers questions about product demand, trends, and inventory recommendations.
"""
import logging
from typing import Any, Dict, List

from app.core.config import settings
from app.ml.forecaster import predict_demand

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Demand Forecasting Expert for a retail company.
You have access to sales history and ML-generated demand forecasts.
Your job is to:
- Interpret demand forecasts clearly
- Identify trends (rising, falling, seasonal)
- Recommend inventory levels and reorder points
- Flag potential stockout or overstock risks

Always be concise, data-driven, and actionable.
"""


def _mock_llm_response(user_message: str, context: str) -> str:
    """Simple rule-based response when Azure OpenAI is not configured."""
    msg = user_message.lower()
    if "forecast" in msg or "demand" in msg or "predict" in msg:
        return (
            f"Based on the forecast data:\n{context}\n\n"
            "The model predicts stable demand with slight weekly seasonality. "
            "I recommend maintaining safety stock at 1.5x the average daily demand."
        )
    if "trend" in msg:
        return (
            "The sales trend shows moderate growth over the past 30 days. "
            "Weekend demand is typically 20-30% higher than weekdays."
        )
    if "reorder" in msg or "stock" in msg or "inventory" in msg:
        return (
            "Based on current demand forecasts, I recommend setting reorder points "
            "at 7-day lead time demand + 2 standard deviations as safety stock."
        )
    return (
        f"Here is the demand analysis based on available data:\n{context}\n\n"
        "Please ask about specific products, trends, or inventory recommendations."
    )


def _azure_llm_response(user_message: str, context: str) -> str:
    """Call Azure OpenAI for a response."""
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Forecast context:\n{context}\n\nQuestion: {user_message}"},
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
        return _mock_llm_response(user_message, context)


class DemandForecastAgent:
    """Agent that answers demand-related questions using ML forecasts."""

    name = "DemandForecastAgent"

    def run(self, user_message: str, product_id: str = "P001", history: List[Dict] = None) -> str:
        logger.info("[DemandForecastAgent] Query: %s", user_message)

        # Get forecast data as context
        forecast = predict_demand(product_id, history or [], forecast_days=7)
        context_lines = [
            f"Product: {product_id}",
            "7-Day Demand Forecast:",
        ]
        for f in forecast:
            context_lines.append(
                f"  {f['date']}: {f['predicted_demand']} units "
                f"(CI: {f['lower']} – {f['upper']})"
            )
        context = "\n".join(context_lines)

        if settings.use_azure_openai:
            return _azure_llm_response(user_message, context)
        return _mock_llm_response(user_message, context)
