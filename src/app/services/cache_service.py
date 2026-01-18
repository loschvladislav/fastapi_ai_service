"""Redis cache service for caching AI responses."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching AI responses in Redis."""

    def __init__(self):
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self._redis = None

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis is not None

    def _generate_key(self, prefix: str, data: dict[str, Any]) -> str:
        """Generate a cache key from request data."""
        data_str = json.dumps(data, sort_keys=True)
        hash_value = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"

    async def get(self, prefix: str, request_data: dict[str, Any]) -> str | None:
        """Get cached response."""
        if not self._redis:
            return None

        key = self._generate_key(prefix, request_data)
        try:
            cached = await self._redis.get(key)
            if cached:
                logger.debug(f"Cache hit for key: {key}")
                return cached
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(
        self,
        prefix: str,
        request_data: dict[str, Any],
        response: str,
        ttl: int | None = None,
    ) -> None:
        """Cache a response."""
        if not self._redis:
            return

        key = self._generate_key(prefix, request_data)
        ttl = ttl or settings.cache_ttl_seconds

        try:
            await self._redis.set(key, response, ex=ttl)
            logger.debug(f"Cached response for key: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def delete(self, prefix: str, request_data: dict[str, Any]) -> None:
        """Delete a cached response."""
        if not self._redis:
            return

        key = self._generate_key(prefix, request_data)
        try:
            await self._redis.delete(key)
            logger.debug(f"Deleted cache key: {key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all cached responses with a given prefix."""
        if not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(f"{prefix}:*"):
                keys.append(key)
            if keys:
                await self._redis.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache keys with prefix: {prefix}")
            return len(keys)
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0


# Global cache service instance
cache_service = CacheService()
