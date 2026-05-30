"""
POST /api/agent – Multi-agent chat endpoint.
"""
import logging
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import AgentOrchestrator
from app.db.database import get_db
from app.db.models import AgentConversation

logger = logging.getLogger(__name__)
router = APIRouter()

_orchestrator = AgentOrchestrator()


class AgentRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    session_id: str
    agent: str
    intent: str
    response: str
    data: Optional[Dict[str, Any]] = None


@router.post("/agent", response_model=AgentResponse)
async def chat_with_agent(payload: AgentRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to the multi-agent system and get a response."""
    session_id = payload.session_id or str(uuid.uuid4())

    try:
        result = _orchestrator.run(payload.message, context=payload.context or {})

        # Persist conversation
        conv = AgentConversation(
            session_id=session_id,
            agent_type=result.get("agent", "unknown"),
            user_message=payload.message,
            agent_response=result.get("response", ""),
        )
        db.add(conv)
        await db.commit()

        logger.info(
            "Agent response: session=%s agent=%s intent=%s",
            session_id, result.get("agent"), result.get("intent"),
        )

        return AgentResponse(
            session_id=session_id,
            agent=result.get("agent", "unknown"),
            intent=result.get("intent", "unknown"),
            response=result.get("response", ""),
            data=result.get("data"),
        )

    except Exception as exc:
        logger.error("Agent endpoint error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")
