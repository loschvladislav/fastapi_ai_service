import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.models.usage import UsageRecord
from app.schemas.usage import UsageSummary


async def record_usage(
    db: AsyncSession,
    api_key: APIKey,
    endpoint: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> UsageRecord:
    """Record API usage for an API key."""
    usage = UsageRecord(
        api_key_id=api_key.id,
        endpoint=endpoint,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        tokens_used=prompt_tokens + completion_tokens,
    )

    db.add(usage)
    await db.commit()
    await db.refresh(usage)

    return usage


async def get_usage_records(
    db: AsyncSession,
    api_key_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    since: datetime | None = None,
) -> list[UsageRecord]:
    """Get usage records for an API key."""
    query = (
        select(UsageRecord)
        .where(UsageRecord.api_key_id == api_key_id)
        .order_by(UsageRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    if since:
        query = query.where(UsageRecord.created_at >= since)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_usage_summary(
    db: AsyncSession,
    api_key_id: uuid.UUID,
    days: int = 30,
) -> UsageSummary:
    """Get aggregated usage summary for an API key."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)

    query = select(
        func.count(UsageRecord.id).label("total_requests"),
        func.coalesce(func.sum(UsageRecord.tokens_used), 0).label("total_tokens"),
        func.coalesce(func.sum(UsageRecord.prompt_tokens), 0).label("total_prompt_tokens"),
        func.coalesce(func.sum(UsageRecord.completion_tokens), 0).label("total_completion_tokens"),
    ).where(
        UsageRecord.api_key_id == api_key_id,
        UsageRecord.created_at >= period_start,
    )

    result = await db.execute(query)
    row = result.one()

    return UsageSummary(
        total_requests=row.total_requests,
        total_tokens=row.total_tokens,
        total_prompt_tokens=row.total_prompt_tokens,
        total_completion_tokens=row.total_completion_tokens,
        period_start=period_start,
        period_end=now,
    )
