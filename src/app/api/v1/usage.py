import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.usage import UsageRecordResponse, UsageSummary
from app.services import api_key_service, usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/{key_id}", response_model=list[UsageRecordResponse])
async def get_usage_records(
    key_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    since: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get usage records for an API key."""
    # Verify API key exists
    api_key = await api_key_service.get_api_key_by_id(db, key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    records = await usage_service.get_usage_records(
        db, key_id, skip=skip, limit=limit, since=since
    )
    return records


@router.get("/{key_id}/summary", response_model=UsageSummary)
async def get_usage_summary(
    key_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated usage summary for an API key."""
    # Verify API key exists
    api_key = await api_key_service.get_api_key_by_id(db, key_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    summary = await usage_service.get_usage_summary(db, key_id, days=days)
    return summary
