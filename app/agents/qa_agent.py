"""
Customer Q&A Agent (RAG-powered)
Answers customer questions using the product/policy knowledge base.
"""
import logging

from app.core.config import settings
from app.rag.retriever import retrieve, format_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful retail customer assistant.
You answer questions about products, store policies, promotions, and services.
Use ONLY the provided context to answer. If the answer is not in the context, say so politely.
Be friendly, concise, and helpful.
"""


def _mock_llm_response(user_message: str, context: str) -> str:
    """Rule-based fallback when Azure OpenAI is not configured."""
    msg = user_message.lower()
    if context and "No relevant" not in context:
        return (
            f"Based on our knowledge base:\n\n{context}\n\n"
            "Is there anything else I can help you with?"
        )
    if "return" in msg or "refund" in msg:
        return (
            "Our return policy allows returns within 30 days of purchase with a receipt. "
            "Items must be in original condition. Refunds are processed within 5-7 business days."
        )
    if "hour" in msg or "open" in msg or "close" in msg:
        return "Our stores are open Monday–Saturday 9AM–9PM and Sunday 10AM–6PM."
    if "discount" in msg or "sale" in msg or "promo" in msg:
        return (
            "We currently have seasonal promotions running. "
            "Check our app or website for the latest deals and member-exclusive offers."
        )
    if "delivery" in msg or "shipping" in msg:
        return (
            "We offer free delivery on orders over $50. Standard delivery takes 3-5 business days. "
            "Express delivery (1-2 days) is available for an additional fee."
        )
    return (
        "Thank you for your question. I wasn't able to find specific information about that. "
        "Please contact our customer support team at support@retailstore.com for further assistance."
    )


def _azure_llm_response(user_message: str, context: str) -> str:
    """Call Azure OpenAI for a RAG-grounded response."""
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context from knowledge base:\n{context}\n\nCustomer question: {user_message}",
            },
        ]
        response = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=messages,
            max_tokens=400,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("Azure OpenAI call failed: %s", exc)
        return _mock_llm_response(user_message, context)


class CustomerQAAgent:
    """RAG-powered agent for customer Q&A."""

    name = "CustomerQAAgent"

    def run(self, user_message: str) -> str:
        logger.info("[CustomerQAAgent] Query: %s", user_message)

        # Retrieve relevant documents
        docs = retrieve(user_message, k=3)
        context = format_context(docs)

        if settings.use_azure_openai:
            return _azure_llm_response(user_message, context)
        return _mock_llm_response(user_message, context)
