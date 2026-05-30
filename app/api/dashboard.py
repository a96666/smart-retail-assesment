"""
GET /api/dashboard – Aggregated metrics for the Power BI / frontend dashboard.
"""
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import SalesRecord, AnomalyAlert, ForecastResult

logger = logging.getLogger(__name__)
router = APIRouter()


class TopProduct(BaseModel):
    product_id: str
    product_name: str
    total_revenue: float
    total_quantity: int


class DashboardMetrics(BaseModel):
    total_revenue_30d: float
    total_transactions_30d: int
    anomaly_count_7d: int
    top_products: list
    revenue_by_category: dict
    daily_revenue_trend: list


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Return aggregated metrics for the dashboard."""
    try:
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        # Total revenue last 30 days
        rev_result = await db.execute(
            select(func.sum(SalesRecord.total_revenue), func.count(SalesRecord.id))
            .where(SalesRecord.sale_date >= thirty_days_ago)
        )
        rev_row = rev_result.one()
        total_revenue = float(rev_row[0] or 0.0)
        total_transactions = int(rev_row[1] or 0)

        # Anomaly count last 7 days
        anomaly_result = await db.execute(
            select(func.count(AnomalyAlert.id))
            .where(AnomalyAlert.is_anomaly == True)  # noqa: E712
            .where(AnomalyAlert.created_at >= seven_days_ago)
        )
        anomaly_count = int(anomaly_result.scalar() or 0)

        # Top 5 products by revenue
        top_result = await db.execute(
            select(
                SalesRecord.product_id,
                SalesRecord.product_name,
                func.sum(SalesRecord.total_revenue).label("total_revenue"),
                func.sum(SalesRecord.quantity).label("total_quantity"),
            )
            .where(SalesRecord.sale_date >= thirty_days_ago)
            .group_by(SalesRecord.product_id, SalesRecord.product_name)
            .order_by(desc("total_revenue"))
            .limit(5)
        )
        top_products = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "total_revenue": round(float(row.total_revenue), 2),
                "total_quantity": int(row.total_quantity),
            }
            for row in top_result.all()
        ]

        # Revenue by category
        cat_result = await db.execute(
            select(
                SalesRecord.category,
                func.sum(SalesRecord.total_revenue).label("revenue"),
            )
            .where(SalesRecord.sale_date >= thirty_days_ago)
            .group_by(SalesRecord.category)
        )
        revenue_by_category = {
            row.category: round(float(row.revenue), 2)
            for row in cat_result.all()
        }

        # Daily revenue trend (last 14 days)
        trend_result = await db.execute(
            select(
                func.date(SalesRecord.sale_date).label("day"),
                func.sum(SalesRecord.total_revenue).label("revenue"),
            )
            .where(SalesRecord.sale_date >= now - timedelta(days=14))
            .group_by(func.date(SalesRecord.sale_date))
            .order_by("day")
        )
        daily_trend = [
            {"date": str(row.day), "revenue": round(float(row.revenue), 2)}
            for row in trend_result.all()
        ]

        return DashboardMetrics(
            total_revenue_30d=round(total_revenue, 2),
            total_transactions_30d=total_transactions,
            anomaly_count_7d=anomaly_count,
            top_products=top_products,
            revenue_by_category=revenue_by_category,
            daily_revenue_trend=daily_trend,
        )

    except Exception as exc:
        logger.error("Dashboard error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load dashboard metrics")
