import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from openai import APIConnectionError, AuthenticationError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentAPIKey
from app.core.rate_limit import get_rate_limit, limiter
from app.database import get_db
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.services.cache_service import cache_service
from app.services.openai_service import summarize_text
from app.services.usage_service import record_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summarize", tags=["summarize"])


@router.post("", response_model=SummarizeResponse)
@limiter.limit(get_rate_limit())
async def create_summary(
    request: Request,
    summarize_request: SummarizeRequest,
    api_key: CurrentAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Summarize text using AI.

    Requires API key in X-API-Key header.

    Supports three styles:
    - concise: Brief summary focusing on key points
    - detailed: Comprehensive summary with more context
    - bullet_points: Summary as a bulleted list
    """
    logger.info(
        "Summarize request received",
        extra={
            "text_length": len(summarize_request.text),
            "style": summarize_request.style,
            "api_key": api_key.key_prefix,
        },
    )

    # Try to get cached response
    cache_key_data = {
        "text": summarize_request.text,
        "max_length": summarize_request.max_length,
        "style": summarize_request.style,
    }
    cached = await cache_service.get("summarize", cache_key_data)
    if cached:
        logger.info("Returning cached summarize response")
        cached_data = json.loads(cached)
        return SummarizeResponse(**cached_data)

    try:
        response = await summarize_text(summarize_request)

        # Cache the response
        await cache_service.set("summarize", cache_key_data, json.dumps(response.model_dump()))

        # Record usage
        await record_usage(
            db=db,
            api_key=api_key,
            endpoint="/api/v1/summarize",
            prompt_tokens=response.usage.get("prompt_tokens", 0),
            completion_tokens=response.usage.get("completion_tokens", 0),
        )

        return response

    except AuthenticationError:
        logger.error("OpenAI authentication failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service configuration error",
        )
    except RateLimitError:
        logger.warning("OpenAI rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI service is busy, please try again later",
        )
    except APIConnectionError:
        logger.error("Failed to connect to OpenAI")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable",
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
