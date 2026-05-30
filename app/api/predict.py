"""
GET /api/predict – Demand forecast for a product.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import SalesRecord, ForecastResult
from app.ml.forecaster import predict_demand

logger = logging.getLogger(__name__)
router = APIRouter()


class ForecastPoint(BaseModel):
    date: str
    predicted_demand: float
    lower: float
    upper: float


class PredictResponse(BaseModel):
    product_id: str
    forecast_days: int
    forecast: List[ForecastPoint]


@router.get("/predict", response_model=PredictResponse)
async def get_forecast(
    product_id: str = Query(..., example="P001"),
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """Generate demand forecast for a product using historical sales data."""
    try:
        # Fetch last 90 days of history from DB
        result = await db.execute(
            select(SalesRecord)
            .where(SalesRecord.product_id == product_id)
            .order_by(desc(SalesRecord.sale_date))
            .limit(90)
        )
        rows = result.scalars().all()

        history = [
            {"date": str(r.sale_date.date()), "quantity": r.quantity}
            for r in reversed(rows)
        ]

        forecast_data = predict_demand(product_id, history, forecast_days=days)

        # Persist forecast results
        for f in forecast_data:
            from datetime import datetime
            fr = ForecastResult(
                product_id=product_id,
                forecast_date=datetime.strptime(f["date"], "%Y-%m-%d"),
                predicted_demand=f["predicted_demand"],
                confidence_lower=f["lower"],
                confidence_upper=f["upper"],
            )
            db.add(fr)
        await db.commit()

        logger.info("Forecast generated for %s (%d days)", product_id, days)
        return PredictResponse(
            product_id=product_id,
            forecast_days=days,
            forecast=[ForecastPoint(**f) for f in forecast_data],
        )

    except Exception as exc:
        logger.error("Predict error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(exc)}")
