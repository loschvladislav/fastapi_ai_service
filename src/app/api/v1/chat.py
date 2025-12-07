import logging

from fastapi import APIRouter, HTTPException, Request, status
from openai import APIConnectionError, AuthenticationError, RateLimitError

from app.core.rate_limit import get_rate_limit, limiter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openai_service import chat_completion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(get_rate_limit())
async def create_chat_completion(request: Request, chat_request: ChatRequest):
    """
    Send a chat completion request to OpenAI.

    Rate limited to prevent abuse.
    """
    logger.info(
        "Chat request received",
        extra={"model": chat_request.model, "message_count": len(chat_request.messages)},
    )

    try:
        response = await chat_completion(chat_request)
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
