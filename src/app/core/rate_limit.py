from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address)


def get_rate_limit() -> str:
    """Get rate limit string for endpoints."""
    return f"{settings.rate_limit_per_minute}/minute"
