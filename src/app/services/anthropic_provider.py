"""Anthropic (Claude) implementation of AIProvider."""

import json
import logging
from typing import AsyncGenerator

import httpx

from app.config import settings
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.schemas.translate import TranslateRequest, TranslateResponse
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) implementation of AIProvider."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _build_messages(self, messages: list[ChatMessage]) -> tuple[str | None, list[dict]]:
        """Separate system message from user/assistant messages (Anthropic format)."""
        system = None
        api_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})
        return system, api_messages

    async def chat(self, request: ChatRequest) -> ChatResponse:
        logger.info(
            "Anthropic request",
            extra={
                "model": request.model,
                "message_count": len(request.messages),
                "max_tokens": request.max_tokens,
            },
        )

        system, messages = self._build_messages(request.messages)

        body = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=self.headers,
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        content = data["content"][0]["text"]
        usage = data.get("usage", {})

        logger.info(
            "Anthropic response",
            extra={
                "model": data["model"],
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )

        return ChatResponse(
            message=ChatMessage(role="assistant", content=content),
            model=data["model"],
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        logger.info(
            "Anthropic streaming request",
            extra={
                "model": request.model,
                "message_count": len(request.messages),
                "max_tokens": request.max_tokens,
            },
        )

        system, messages = self._build_messages(request.messages)

        body = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
            "stream": True,
        }
        if system:
            body["system"] = system

        full_content = ""

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                ANTHROPIC_API_URL,
                headers=self.headers,
                json=body,
                timeout=60.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    event_data = json.loads(line[6:])
                    event_type = event_data.get("type")

                    if event_type == "content_block_delta":
                        token = event_data["delta"].get("text", "")
                        if token:
                            full_content += token
                            yield f"data: {json.dumps({'token': token})}\n\n"

        yield f"data: {json.dumps({'done': True, 'full_text': full_content})}\n\n"

        logger.info(
            "Anthropic streaming response complete",
            extra={
                "model": request.model,
                "content_length": len(full_content),
            },
        )

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        logger.info(
            "Summarize request (Anthropic)",
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

        system_prompt = (
            f"You are a professional summarizer. {style_prompts[request.style]} "
            f"Keep the summary under {request.max_length} words. Focus on key points and main ideas."
        )

        body = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Summarize the following text:\n\n{request.text}"},
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=self.headers,
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        summary = data["content"][0]["text"]
        usage = data.get("usage", {})

        logger.info(
            "Summarize response (Anthropic)",
            extra={
                "original_length": len(request.text),
                "summary_length": len(summary),
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )

        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text),
            summary_length=len(summary),
            model=data["model"],
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        )

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        logger.info(
            "Translate request (Anthropic)",
            extra={
                "text_length": len(request.text),
                "source_language": request.source_language,
                "target_language": request.target_language,
            },
        )

        if request.source_language == "auto":
            system_prompt = (
                f"You are a professional translator. "
                f"Detect the source language and translate the text to {request.target_language}. "
                f"Only output the translation, nothing else."
            )
        else:
            system_prompt = (
                f"You are a professional translator. "
                f"Translate the text from {request.source_language} to {request.target_language}. "
                f"Only output the translation, nothing else."
            )

        body = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": request.text},
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=self.headers,
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        translated = data["content"][0]["text"]
        usage = data.get("usage", {})

        detected_source = request.source_language
        if request.source_language == "auto":
            detected_source = "auto-detected"

        logger.info(
            "Translate response (Anthropic)",
            extra={
                "source_language": detected_source,
                "target_language": request.target_language,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )

        return TranslateResponse(
            translated_text=translated,
            source_language=detected_source,
            target_language=request.target_language,
            model=data["model"],
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        )
