import json
import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI implementation of AIProvider."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        logger.info(
            "OpenAI request",
            extra={
                "model": request.model,
                "message_count": len(request.messages),
                "max_tokens": request.max_tokens,
            },
        )

        try:
            response = await self.client.chat.completions.create(
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

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        logger.info(
            "OpenAI streaming request",
            extra={
                "model": request.model,
                "message_count": len(request.messages),
                "max_tokens": request.max_tokens,
            },
        )

        full_content = ""

        try:
            stream = await self.client.chat.completions.create(
                model=request.model,
                messages=[{"role": m.role, "content": m.content} for m in request.messages],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'done': True, 'full_text': full_content})}\n\n"

            logger.info(
                "OpenAI streaming response complete",
                extra={
                    "model": request.model,
                    "content_length": len(full_content),
                },
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}", extra={"error_type": type(e).__name__})
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            raise

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        logger.info(
            "Summarize request",
            extra={
                "text_length": len(request.text),
                "max_length": request.max_length,
                "style": request.style,
            },
        )

        style_prompts = {
            "concise": "Provide a brief, concise summary.",
            "detailed": "Provide a comprehensive, detailed summary.",
            "bullet_points": "Provide a summary in bullet points.",
        }

        system_prompt = f"""You are a professional summarizer. {style_prompts[request.style]}
Keep the summary under {request.max_length} words. Focus on key points and main ideas."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Summarize the following text:\n\n{request.text}"},
                ],
                max_tokens=1500,
                temperature=0.5,
            )

            summary = response.choices[0].message.content or ""
            usage = response.usage

            logger.info(
                "Summarize response",
                extra={
                    "original_length": len(request.text),
                    "summary_length": len(summary),
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            )

            return SummarizeResponse(
                summary=summary,
                original_length=len(request.text),
                summary_length=len(summary),
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

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        logger.info(
            "Translate request",
            extra={
                "text_length": len(request.text),
                "source_language": request.source_language,
                "target_language": request.target_language,
            },
        )

        if request.source_language == "auto":
            system_prompt = f"""You are a professional translator.
Detect the source language and translate the text to {request.target_language}.
Only output the translation, nothing else."""
        else:
            system_prompt = f"""You are a professional translator.
Translate the text from {request.source_language} to {request.target_language}.
Only output the translation, nothing else."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text},
                ],
                max_tokens=2000,
                temperature=0.3,
            )

            translated = response.choices[0].message.content or ""
            usage = response.usage

            detected_source = request.source_language
            if request.source_language == "auto":
                detected_source = "auto-detected"

            logger.info(
                "Translate response",
                extra={
                    "source_language": detected_source,
                    "target_language": request.target_language,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            )

            return TranslateResponse(
                translated_text=translated,
                source_language=detected_source,
                target_language=request.target_language,
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
