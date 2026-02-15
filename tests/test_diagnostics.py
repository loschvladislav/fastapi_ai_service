"""Tests for the diagnostics endpoints (EXPLAIN ANALYZE)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import UsageRecord


class TestDiagnosticsEndpoints:
    """Test EXPLAIN ANALYZE diagnostic endpoints."""

    async def test_explain_usage_records(self, client: AsyncClient, db: AsyncSession):
        """Test EXPLAIN ANALYZE on usage records query returns a valid plan."""
        # Create API key
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Diag Test Key"})
        key_id = create_resp.json()["id"]

        # Add a usage record so the table is not empty
        usage = UsageRecord(
            api_key_id=uuid.UUID(key_id),
            endpoint="/api/v1/chat",
            tokens_used=100,
            prompt_tokens=40,
            completion_tokens=60,
        )
        db.add(usage)
        await db.commit()

        response = await client.get(
            f"/api/v1/diagnostics/explain/usage-records?api_key_id={key_id}&days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "get_usage_records"
        assert isinstance(data["plan"], list)
        assert len(data["plan"]) > 0

        # Plan should contain execution info
        plan_text = " ".join(data["plan"])
        assert "Execution Time" in plan_text

    async def test_explain_usage_summary(self, client: AsyncClient, db: AsyncSession):
        """Test EXPLAIN ANALYZE on usage summary aggregation query."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Summary Diag Key"})
        key_id = create_resp.json()["id"]

        response = await client.get(
            f"/api/v1/diagnostics/explain/usage-summary?api_key_id={key_id}&days=7"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "get_usage_summary"
        assert isinstance(data["plan"], list)
        assert len(data["plan"]) > 0

        plan_text = " ".join(data["plan"])
        assert "Execution Time" in plan_text

    async def test_explain_api_key_lookup(self, client: AsyncClient):
        """Test EXPLAIN ANALYZE on API key lookup by hash."""
        response = await client.get(
            "/api/v1/diagnostics/explain/api-key-lookup?key_hash=abc123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "get_api_key_by_hash"
        assert isinstance(data["plan"], list)

        # API key lookup should use the unique index
        plan_text = " ".join(data["plan"])
        assert "Index Scan" in plan_text
        assert "api_keys_key_hash_key" in plan_text

    async def test_explain_usage_records_invalid_days(self, client: AsyncClient):
        """Test that invalid days parameter is rejected."""
        key_id = uuid.uuid4()

        response = await client.get(
            f"/api/v1/diagnostics/explain/usage-records?api_key_id={key_id}&days=0"
        )
        assert response.status_code == 422

        response = await client.get(
            f"/api/v1/diagnostics/explain/usage-records?api_key_id={key_id}&days=999"
        )
        assert response.status_code == 422

    async def test_explain_usage_records_missing_api_key_id(self, client: AsyncClient):
        """Test that missing api_key_id parameter is rejected."""
        response = await client.get("/api/v1/diagnostics/explain/usage-records")
        assert response.status_code == 422
