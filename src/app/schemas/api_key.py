import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    rate_limit_per_minute: int
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    """Response after creating API key - includes the full key (shown only once)."""

    key: str


class APIKeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=1000)
