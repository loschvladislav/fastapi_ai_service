import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from openai import APIConnectionError, AuthenticationError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentAPIKey
from app.core.rate_limit import get_rate_limit, limiter
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.cache_service import cache_service
from app.services.openai_service import chat_completion, chat_completion_stream
from app.services.usage_service import record_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(get_rate_limit())
async def create_chat_completion(
    request: Request,
    chat_request: ChatRequest,
    api_key: CurrentAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat completion request to OpenAI.

    Requires API key in X-API-Key header.
    """
    logger.info(
        "Chat request received",
        extra={
            "model": chat_request.model,
            "message_count": len(chat_request.messages),
            "api_key": api_key.key_prefix,
        },
    )

    # Try to get cached response
    cache_key_data = {
        "messages": [m.model_dump() for m in chat_request.messages],
        "model": chat_request.model,
        "max_tokens": chat_request.max_tokens,
        "temperature": chat_request.temperature,
    }
    cached = await cache_service.get("chat", cache_key_data)
    if cached:
        logger.info("Returning cached chat response")
        cached_data = json.loads(cached)
        return ChatResponse(**cached_data)

    try:
        response = await chat_completion(chat_request)

        # Cache the response
        await cache_service.set("chat", cache_key_data, json.dumps(response.model_dump()))

        # Record usage
        await record_usage(
            db=db,
            api_key=api_key,
            endpoint="/api/v1/chat",
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


@router.post("/stream")
@limiter.limit(get_rate_limit())
async def create_chat_completion_stream(
    request: Request,
    chat_request: ChatRequest,
    api_key: CurrentAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream chat completion from OpenAI using Server-Sent Events.

    Returns tokens as they are generated, providing real-time response.

    Requires API key in X-API-Key header.
    """
    logger.info(
        "Streaming chat request received",
        extra={
            "model": chat_request.model,
            "message_count": len(chat_request.messages),
            "api_key": api_key.key_prefix,
        },
    )

    # Record usage (approximate for streaming - exact tokens unknown upfront)
    await record_usage(
        db=db,
        api_key=api_key,
        endpoint="/api/v1/chat/stream",
        prompt_tokens=0,
        completion_tokens=0,
    )

    return StreamingResponse(
        chat_completion_stream(chat_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
