import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from openai import APIConnectionError, AuthenticationError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentAPIKey
from app.core.rate_limit import get_rate_limit, limiter
from app.database import get_db
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.cache_service import cache_service
from app.services.ai_provider import ai_provider
from app.services.usage_service import record_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["translate"])


@router.post("", response_model=TranslateResponse)
@limiter.limit(get_rate_limit())
async def create_translation(
    request: Request,
    translate_request: TranslateRequest,
    api_key: CurrentAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Translate text using AI.

    Requires API key in X-API-Key header.

    Supports automatic language detection when source_language is set to "auto".
    """
    logger.info(
        "Translate request received",
        extra={
            "text_length": len(translate_request.text),
            "source": translate_request.source_language,
            "target": translate_request.target_language,
            "api_key": api_key.key_prefix,
        },
    )

    # Try to get cached response
    cache_key_data = {
        "text": translate_request.text,
        "source_language": translate_request.source_language,
        "target_language": translate_request.target_language,
    }
    cached = await cache_service.get("translate", cache_key_data)
    if cached:
        logger.info("Returning cached translate response")
        cached_data = json.loads(cached)
        return TranslateResponse(**cached_data)

    try:
        response = await ai_provider.translate(translate_request)

        # Cache the response
        await cache_service.set("translate", cache_key_data, json.dumps(response.model_dump()))

        # Record usage
        await record_usage(
            db=db,
            api_key=api_key,
            endpoint="/api/v1/translate",
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
