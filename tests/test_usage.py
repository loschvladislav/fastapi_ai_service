import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import UsageRecord


class TestUsageEndpoints:
    async def test_get_usage_records_empty(self, client: AsyncClient):
        """Test getting usage records for a key with no usage."""
        # Create API key
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Usage Test Key"})
        key_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/usage/{key_id}")

        assert response.status_code == 200
        assert response.json() == []

    async def test_get_usage_records_not_found(self, client: AsyncClient):
        """Test getting usage for non-existent key."""
        response = await client.get("/api/v1/usage/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_get_usage_summary_empty(self, client: AsyncClient):
        """Test getting usage summary with no usage."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Summary Test Key"})
        key_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/usage/{key_id}/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 0
        assert data["total_tokens"] == 0
        assert data["total_prompt_tokens"] == 0
        assert data["total_completion_tokens"] == 0

    async def test_get_usage_summary_not_found(self, client: AsyncClient):
        """Test getting summary for non-existent key."""
        response = await client.get("/api/v1/usage/00000000-0000-0000-0000-000000000000/summary")
        assert response.status_code == 404

    async def test_get_usage_with_records(self, client: AsyncClient, db: AsyncSession):
        """Test getting usage records with actual data."""
        # Create API key
        create_resp = await client.post("/api/v1/api-keys", json={"name": "With Records Key"})
        key_data = create_resp.json()
        key_id = key_data["id"]

        # Add usage records directly to database
        usage1 = UsageRecord(
            api_key_id=uuid.UUID(key_id),
            endpoint="/api/v1/chat",
            tokens_used=100,
            prompt_tokens=40,
            completion_tokens=60,
        )
        usage2 = UsageRecord(
            api_key_id=uuid.UUID(key_id),
            endpoint="/api/v1/summarize",
            tokens_used=50,
            prompt_tokens=20,
            completion_tokens=30,
        )
        db.add(usage1)
        db.add(usage2)
        await db.commit()

        # Get records
        response = await client.get(f"/api/v1/usage/{key_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get summary
        summary_resp = await client.get(f"/api/v1/usage/{key_id}/summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["total_requests"] == 2
        assert summary["total_tokens"] == 150
        assert summary["total_prompt_tokens"] == 60
        assert summary["total_completion_tokens"] == 90

    async def test_get_usage_with_pagination(self, client: AsyncClient, db: AsyncSession):
        """Test usage records pagination."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Pagination Key"})
        key_id = create_resp.json()["id"]

        # Add 5 records
        for i in range(5):
            usage = UsageRecord(
                api_key_id=uuid.UUID(key_id),
                endpoint=f"/api/v1/test{i}",
                tokens_used=10,
                prompt_tokens=5,
                completion_tokens=5,
            )
            db.add(usage)
        await db.commit()

        # Get with limit
        response = await client.get(f"/api/v1/usage/{key_id}?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get with skip
        response = await client.get(f"/api/v1/usage/{key_id}?skip=3&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 2
