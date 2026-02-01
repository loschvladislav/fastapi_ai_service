from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.summarize import SummarizeResponse
from app.services.ai_provider import ai_provider


class TestSummarizeEndpoint:
    async def test_summarize_requires_api_key(self, client: AsyncClient):
        """Test that summarize endpoint requires API key."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": "This is a long enough text to summarize properly.",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing API key"

    async def test_summarize_success(self, client: AsyncClient, api_key_headers: dict):
        """Test successful text summarization."""
        mock_response = SummarizeResponse(
            summary="This is a summary of the text.",
            original_length=500,
            summary_length=35,
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        )

        with patch.object(ai_provider, "summarize", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/summarize",
                json={
                    "text": "This is a long text that needs to be summarized. " * 20,
                    "max_length": 100,
                    "style": "concise",
                },
                headers=api_key_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert data["model"] == "gpt-3.5-turbo"

    async def test_summarize_bullet_points(self, client: AsyncClient, api_key_headers: dict):
        """Test summarization with bullet points style."""
        mock_response = SummarizeResponse(
            summary="- Point 1\n- Point 2\n- Point 3",
            original_length=500,
            summary_length=30,
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 100, "completion_tokens": 15, "total_tokens": 115},
        )

        with patch.object(ai_provider, "summarize", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await client.post(
                "/api/v1/summarize",
                json={
                    "text": "This is a text with multiple points. " * 20,
                    "style": "bullet_points",
                },
                headers=api_key_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "-" in data["summary"]

    async def test_summarize_validation_text_too_short(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for text too short."""
        response = await client.post(
            "/api/v1/summarize",
            json={"text": "Short"},  # Less than 10 chars
            headers=api_key_headers,
        )
        assert response.status_code == 422

    async def test_summarize_invalid_style(self, client: AsyncClient, api_key_headers: dict):
        """Test validation error for invalid style."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": "This is a long enough text to summarize.",
                "style": "invalid_style",
            },
            headers=api_key_headers,
        )
        assert response.status_code == 422

    async def test_summarize_max_length_validation(self, client: AsyncClient, api_key_headers: dict):
        """Test max_length must be between 50 and 1000."""
        response = await client.post(
            "/api/v1/summarize",
            json={
                "text": "This is a long enough text to summarize.",
                "max_length": 10,  # Too small
            },
            headers=api_key_headers,
        )
        assert response.status_code == 422
