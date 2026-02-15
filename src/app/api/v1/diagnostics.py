"""Diagnostic endpoints for query performance analysis using EXPLAIN ANALYZE."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


async def run_explain_analyze(db: AsyncSession, query: str, params: dict) -> list[str]:
    """Execute EXPLAIN ANALYZE and return the query plan as a list of lines."""
    result = await db.execute(text(f"EXPLAIN ANALYZE {query}"), params)
    return [row[0] for row in result.fetchall()]


@router.get("/explain/usage-records")
async def explain_usage_records(
    api_key_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Run EXPLAIN ANALYZE on the usage records query (filtered by api_key_id + date range)."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    plan = await run_explain_analyze(
        db,
        """
        SELECT * FROM usage_records
        WHERE api_key_id = :api_key_id AND created_at >= :since
        ORDER BY created_at DESC
        LIMIT 100
        """,
        {"api_key_id": api_key_id, "since": since},
    )

    return {"query": "get_usage_records", "plan": plan}


@router.get("/explain/usage-summary")
async def explain_usage_summary(
    api_key_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Run EXPLAIN ANALYZE on the usage summary aggregation query."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    plan = await run_explain_analyze(
        db,
        """
        SELECT
            COUNT(id) AS total_requests,
            COALESCE(SUM(tokens_used), 0) AS total_tokens,
            COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) AS total_completion_tokens
        FROM usage_records
        WHERE api_key_id = :api_key_id AND created_at >= :since
        """,
        {"api_key_id": api_key_id, "since": since},
    )

    return {"query": "get_usage_summary", "plan": plan}


@router.get("/explain/api-key-lookup")
async def explain_api_key_lookup(
    key_hash: str,
    db: AsyncSession = Depends(get_db),
):
    """Run EXPLAIN ANALYZE on the API key lookup by hash (used on every request)."""
    plan = await run_explain_analyze(
        db,
        "SELECT * FROM api_keys WHERE key_hash = :key_hash",
        {"key_hash": key_hash},
    )

    return {"query": "get_api_key_by_hash", "plan": plan}
