import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyResponse, APIKeyUpdate
from app.services import api_key_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key.

    The full key is returned only once in the response.
    Store it securely - it cannot be retrieved later.
    """
    api_key, raw_key = await api_key_service.create_api_key(db, data)
    logger.info(f"API key created: {api_key.name} ({api_key.key_prefix}...)")

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=raw_key,
        is_active=api_key.is_active,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
    )


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    active_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys."""
    keys = await api_key_service.list_api_keys(db, skip=skip, limit=limit, active_only=active_only)
    return keys


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get API key by ID."""
    api_key = await api_key_service.get_api_key_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return api_key


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: uuid.UUID,
    data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an API key."""
    api_key = await api_key_service.get_api_key_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    updated = await api_key_service.update_api_key(db, api_key, data)
    logger.info(f"API key updated: {updated.name} ({updated.key_prefix}...)")
    return updated


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    api_key = await api_key_service.get_api_key_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    await api_key_service.delete_api_key(db, api_key)
    logger.info(f"API key deleted: {api_key.name} ({api_key.key_prefix}...)")
