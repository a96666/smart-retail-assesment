"""
POST /api/ingest – Ingest sales records into the database.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import SalesRecord

logger = logging.getLogger(__name__)
router = APIRouter()


class SaleItem(BaseModel):
    product_id: str = Field(..., example="P001")
    product_name: str = Field(..., example="Wireless Headphones")
    category: str = Field(..., example="Electronics")
    quantity: int = Field(..., ge=0, example=25)
    unit_price: float = Field(..., gt=0, example=49.99)
    sale_date: str = Field(..., example="2024-06-01")
    store_id: str = Field(..., example="S001")


class IngestRequest(BaseModel):
    records: List[SaleItem] = Field(..., min_length=1)


class IngestResponse(BaseModel):
    message: str
    inserted: int


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_sales(payload: IngestRequest, db: AsyncSession = Depends(get_db)):
    """Ingest one or more sales records into the database."""
    try:
        records = []
        for item in payload.records:
            sale_date = datetime.strptime(item.sale_date, "%Y-%m-%d")
            record = SalesRecord(
                product_id=item.product_id,
                product_name=item.product_name,
                category=item.category,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_revenue=round(item.quantity * item.unit_price, 2),
                sale_date=sale_date,
                store_id=item.store_id,
            )
            records.append(record)

        db.add_all(records)
        await db.commit()

        logger.info("Ingested %d sales records", len(records))
        return IngestResponse(message="Records ingested successfully", inserted=len(records))

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {exc}")
    except Exception as exc:
        logger.error("Ingest error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to ingest records")
