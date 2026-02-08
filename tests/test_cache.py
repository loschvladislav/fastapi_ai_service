"""Tests for the cache service."""

import pytest

from app.services.cache_service import CacheService


@pytest.fixture(autouse=True)
def reset_cache_singleton():
    """Reset CacheService singleton before each test."""
    CacheService._reset_instance()
    yield
    CacheService._reset_instance()


class TestCacheService:
    """Test cache service functionality."""

    def test_singleton_returns_same_instance(self):
        """Test that CacheService always returns the same instance."""
        service1 = CacheService()
        service2 = CacheService()
        assert service1 is service2

    def test_generate_key_consistent(self):
        """Test that same data generates same key."""
        service = CacheService()
        data = {"text": "hello", "model": "gpt-3.5"}

        key1 = service._generate_key("test", data)
        key2 = service._generate_key("test", data)

        assert key1 == key2
        assert key1.startswith("test:")

    def test_generate_key_different_data(self):
        """Test that different data generates different keys."""
        service = CacheService()
        data1 = {"text": "hello"}
        data2 = {"text": "world"}

        key1 = service._generate_key("test", data1)
        key2 = service._generate_key("test", data2)

        assert key1 != key2

    def test_generate_key_order_independent(self):
        """Test that key order in dict doesn't affect key."""
        service = CacheService()
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}

        key1 = service._generate_key("test", data1)
        key2 = service._generate_key("test", data2)

        assert key1 == key2

    def test_is_connected_initially_false(self):
        """Test that service is not connected initially."""
        service = CacheService()
        assert service.is_connected is False

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_connected(self):
        """Test that get returns None when Redis is not connected."""
        service = CacheService()
        result = await service.get("test", {"key": "value"})
        assert result is None

    @pytest.mark.asyncio
    async def test_set_does_nothing_when_not_connected(self):
        """Test that set doesn't raise when Redis is not connected."""
        service = CacheService()
        # Should not raise
        await service.set("test", {"key": "value"}, "response")

    @pytest.mark.asyncio
    async def test_delete_does_nothing_when_not_connected(self):
        """Test that delete doesn't raise when Redis is not connected."""
        service = CacheService()
        # Should not raise
        await service.delete("test", {"key": "value"})

    @pytest.mark.asyncio
    async def test_clear_prefix_returns_zero_when_not_connected(self):
        """Test that clear_prefix returns 0 when Redis is not connected."""
        service = CacheService()
        result = await service.clear_prefix("test")
        assert result == 0


class TestCacheServiceIntegration:
    """Integration tests for cache service (requires Redis)."""

    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connect and disconnect cycle."""
        service = CacheService()

        # Try to connect - may fail if Redis not running
        await service.connect()

        # Disconnect should always work
        await service.disconnect()

    @pytest.mark.asyncio
    async def test_full_cache_cycle(self):
        """Test set, get, delete cycle if Redis is available."""
        service = CacheService()
        await service.connect()

        if not service.is_connected:
            pytest.skip("Redis not available")

        try:
            test_data = {"query": "test"}
            test_response = "cached response"

            # Set
            await service.set("test", test_data, test_response)

            # Get
            result = await service.get("test", test_data)
            assert result == test_response

            # Delete
            await service.delete("test", test_data)

            # Verify deleted
            result = await service.get("test", test_data)
            assert result is None

        finally:
            await service.disconnect()

    @pytest.mark.asyncio
    async def test_clear_prefix(self):
        """Test clearing all keys with a prefix."""
        service = CacheService()
        await service.connect()

        if not service.is_connected:
            pytest.skip("Redis not available")

        try:
            # Set multiple keys
            await service.set("prefix", {"id": 1}, "value1")
            await service.set("prefix", {"id": 2}, "value2")
            await service.set("other", {"id": 1}, "other_value")

            # Clear prefix
            cleared = await service.clear_prefix("prefix")
            assert cleared == 2

            # Verify cleared
            assert await service.get("prefix", {"id": 1}) is None
            assert await service.get("prefix", {"id": 2}) is None

            # Other prefix should remain
            assert await service.get("other", {"id": 1}) == "other_value"

            # Cleanup
            await service.clear_prefix("other")

        finally:
            await service.disconnect()
