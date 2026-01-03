import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_key import APIKey
from app.services import api_key_service

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> APIKey:
    """
    Validate API key from header and return the APIKey model.

    Raises HTTPException if key is missing, invalid, or inactive.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    db_key = await api_key_service.get_api_key_by_raw_key(db, api_key)

    if not db_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not db_key.is_active:
        logger.warning(f"Inactive API key used: {db_key.key_prefix}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is inactive",
        )

    # Update last used timestamp
    await api_key_service.update_last_used(db, db_key)

    return db_key


# Type alias for dependency injection
CurrentAPIKey = Annotated[APIKey, Depends(get_api_key)]
