import pytest
from httpx import AsyncClient


class TestAPIKeyEndpoints:
    async def test_create_api_key(self, client: AsyncClient):
        """Test creating a new API key."""
        response = await client.post(
            "/api/v1/api-keys",
            json={"name": "Test Key", "rate_limit_per_minute": 20},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Key"
        assert data["rate_limit_per_minute"] == 20
        assert data["is_active"] is True
        assert "key" in data
        assert data["key"].startswith("ai_")
        assert "key_prefix" in data

    async def test_create_api_key_default_rate_limit(self, client: AsyncClient):
        """Test creating API key with default rate limit."""
        response = await client.post(
            "/api/v1/api-keys",
            json={"name": "Default Rate Key"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rate_limit_per_minute"] == 10

    async def test_list_api_keys(self, client: AsyncClient):
        """Test listing API keys."""
        # Create two keys
        await client.post("/api/v1/api-keys", json={"name": "Key 1"})
        await client.post("/api/v1/api-keys", json={"name": "Key 2"})

        response = await client.get("/api/v1/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_api_keys_active_only(self, client: AsyncClient):
        """Test listing only active API keys."""
        # Create two keys
        resp1 = await client.post("/api/v1/api-keys", json={"name": "Active Key"})
        resp2 = await client.post("/api/v1/api-keys", json={"name": "Inactive Key"})

        # Deactivate one
        key_id = resp2.json()["id"]
        await client.patch(f"/api/v1/api-keys/{key_id}", json={"is_active": False})

        # List active only
        response = await client.get("/api/v1/api-keys?active_only=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Key"

    async def test_get_api_key(self, client: AsyncClient):
        """Test getting a single API key."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Get Test Key"})
        key_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/api-keys/{key_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test Key"
        # Full key should NOT be in response
        assert "key" not in data

    async def test_get_api_key_not_found(self, client: AsyncClient):
        """Test getting non-existent API key."""
        response = await client.get("/api/v1/api-keys/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_update_api_key(self, client: AsyncClient):
        """Test updating an API key."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "Original Name"})
        key_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"name": "Updated Name", "rate_limit_per_minute": 50},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["rate_limit_per_minute"] == 50

    async def test_deactivate_api_key(self, client: AsyncClient):
        """Test deactivating an API key."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "To Deactivate"})
        key_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/v1/api-keys/{key_id}",
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    async def test_delete_api_key(self, client: AsyncClient):
        """Test deleting an API key."""
        create_resp = await client.post("/api/v1/api-keys", json={"name": "To Delete"})
        key_id = create_resp.json()["id"]

        response = await client.delete(f"/api/v1/api-keys/{key_id}")
        assert response.status_code == 204

        # Verify deleted
        get_resp = await client.get(f"/api/v1/api-keys/{key_id}")
        assert get_resp.status_code == 404

    async def test_delete_api_key_not_found(self, client: AsyncClient):
        """Test deleting non-existent API key."""
        response = await client.delete("/api/v1/api-keys/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    async def test_create_api_key_validation_name_required(self, client: AsyncClient):
        """Test that name is required."""
        response = await client.post("/api/v1/api-keys", json={})
        assert response.status_code == 422

    async def test_create_api_key_validation_rate_limit(self, client: AsyncClient):
        """Test rate limit validation."""
        response = await client.post(
            "/api/v1/api-keys",
            json={"name": "Test", "rate_limit_per_minute": 0},
        )
        assert response.status_code == 422

        response = await client.post(
            "/api/v1/api-keys",
            json={"name": "Test", "rate_limit_per_minute": 10000},
        )
        assert response.status_code == 422
