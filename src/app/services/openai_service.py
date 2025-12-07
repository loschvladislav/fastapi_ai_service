import logging

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def chat_completion(request: ChatRequest) -> ChatResponse:
    """Send a chat completion request to OpenAI."""
    logger.info(
        "OpenAI request",
        extra={
            "model": request.model,
            "message_count": len(request.messages),
            "max_tokens": request.max_tokens,
        },
    )

    try:
        response = await client.chat.completions.create(
            model=request.model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        assistant_message = response.choices[0].message.content
        usage = response.usage

        logger.info(
            "OpenAI response",
            extra={
                "model": request.model,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        )

        return ChatResponse(
            message=ChatMessage(role="assistant", content=assistant_message or ""),
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        )

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}", extra={"error_type": type(e).__name__})
        raise
