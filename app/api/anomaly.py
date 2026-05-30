"""
POST /api/anomaly – Detect anomalies in provided sales records.
GET  /api/anomaly – Retrieve stored anomaly alerts.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.anomaly_agent import AnomalyDetectionAgent
from app.db.database import get_db
from app.db.models import AnomalyAlert

logger = logging.getLogger(__name__)
router = APIRouter()

_agent = AnomalyDetectionAgent()


class SaleRecord(BaseModel):
    product_id: str
    date: str
    quantity: float


class AnomalyRequest(BaseModel):
    records: List[SaleRecord]


class AnomalyItem(BaseModel):
    product_id: str
    date: str
    quantity: float
    is_anomaly: bool
    anomaly_score: float
    description: str


class AnomalyResponse(BaseModel):
    total_records: int
    anomaly_count: int
    anomalies: List[AnomalyItem]
    insight: str


class StoredAlert(BaseModel):
    id: int
    product_id: str
    sale_date: str
    actual_quantity: float
    anomaly_score: float
    is_anomaly: bool
    description: Optional[str]
    created_at: str


@router.post("/anomaly", response_model=AnomalyResponse)
async def detect_anomalies(payload: AnomalyRequest, db: AsyncSession = Depends(get_db)):
    """Run anomaly detection on provided sales records."""
    try:
        records = [r.model_dump() for r in payload.records]
        result = _agent.run(records)

        # Persist anomaly alerts
        for item in result["anomalies"]:
            alert = AnomalyAlert(
                product_id=item["product_id"],
                sale_date=datetime.strptime(item["date"], "%Y-%m-%d"),
                actual_quantity=item["quantity"],
                anomaly_score=item["anomaly_score"],
                is_anomaly=item["is_anomaly"],
                description=item.get("description", ""),
            )
            db.add(alert)
        await db.commit()

        return AnomalyResponse(
            total_records=result["total_records"],
            anomaly_count=result["anomaly_count"],
            anomalies=[AnomalyItem(**a) for a in result["anomalies"]],
            insight=result["insight"],
        )

    except Exception as exc:
        logger.error("Anomaly detection error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(exc)}")


@router.get("/anomaly/alerts", response_model=List[StoredAlert])
async def get_alerts(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Retrieve the most recent anomaly alerts from the database."""
    try:
        result = await db.execute(
            select(AnomalyAlert)
            .where(AnomalyAlert.is_anomaly == True)  # noqa: E712
            .order_by(desc(AnomalyAlert.created_at))
            .limit(limit)
        )
        alerts = result.scalars().all()
        return [
            StoredAlert(
                id=a.id,
                product_id=a.product_id,
                sale_date=str(a.sale_date.date()),
                actual_quantity=a.actual_quantity,
                anomaly_score=a.anomaly_score,
                is_anomaly=a.is_anomaly,
                description=a.description,
                created_at=str(a.created_at),
            )
            for a in alerts
        ]
    except Exception as exc:
        logger.error("Get alerts error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")
