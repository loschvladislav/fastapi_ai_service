import logging

from fastapi import APIRouter, HTTPException, Request, status
from openai import APIConnectionError, AuthenticationError, RateLimitError

from app.core.rate_limit import get_rate_limit, limiter
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.openai_service import translate_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translate", tags=["translate"])


@router.post("", response_model=TranslateResponse)
@limiter.limit(get_rate_limit())
async def create_translation(request: Request, translate_request: TranslateRequest):
    """
    Translate text using AI.

    Supports automatic language detection when source_language is set to "auto".
    """
    logger.info(
        "Translate request received",
        extra={
            "text_length": len(translate_request.text),
            "source": translate_request.source_language,
            "target": translate_request.target_language,
        },
    )

    try:
        response = await translate_text(translate_request)
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
