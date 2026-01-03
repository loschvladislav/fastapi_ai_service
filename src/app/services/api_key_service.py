import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate


def hash_key(key: str) -> str:
    """Create SHA-256 hash of API key."""
    return hashlib.sha256(key.encode()).hexdigest()


async def create_api_key(db: AsyncSession, data: APIKeyCreate) -> tuple[APIKey, str]:
    """Create a new API key. Returns the model and the raw key (shown only once)."""
    raw_key = APIKey.generate_key()
    key_hash = hash_key(raw_key)
    key_prefix = raw_key[:8]

    api_key = APIKey(
        name=data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        rate_limit_per_minute=data.rate_limit_per_minute,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return api_key, raw_key


async def get_api_key_by_id(db: AsyncSession, key_id: uuid.UUID) -> APIKey | None:
    """Get API key by ID."""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    return result.scalar_one_or_none()


async def get_api_key_by_raw_key(db: AsyncSession, raw_key: str) -> APIKey | None:
    """Get API key by raw key value."""
    key_hash = hash_key(raw_key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    return result.scalar_one_or_none()


async def list_api_keys(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[APIKey]:
    """List all API keys with optional filtering."""
    query = select(APIKey).offset(skip).limit(limit).order_by(APIKey.created_at.desc())

    if active_only:
        query = query.where(APIKey.is_active == True)  # noqa: E712

    result = await db.execute(query)
    return list(result.scalars().all())


async def update_api_key(
    db: AsyncSession,
    api_key: APIKey,
    data: APIKeyUpdate,
) -> APIKey:
    """Update API key fields."""
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(api_key, field, value)

    await db.commit()
    await db.refresh(api_key)
    return api_key


async def delete_api_key(db: AsyncSession, api_key: APIKey) -> None:
    """Delete an API key."""
    await db.delete(api_key)
    await db.commit()


async def update_last_used(db: AsyncSession, api_key: APIKey) -> None:
    """Update the last_used_at timestamp."""
    from datetime import datetime, timezone

    api_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()
