from abc import ABC, abstractmethod
from typing import AsyncGenerator

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.summarize import SummarizeRequest, SummarizeResponse
from app.schemas.translate import TranslateRequest, TranslateResponse


class AIProvider(ABC):
    """Abstract base class for AI providers.

    Defines the contract that all AI providers must implement.
    To add a new provider (e.g., Anthropic), create a new class
    that inherits from AIProvider and implement all abstract methods.
    """

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        pass

    @abstractmethod
    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        pass


def get_ai_provider() -> AIProvider:
    """Factory function that creates the AI provider based on config."""
    from app.config import settings

    if settings.ai_provider == "openai":
        from app.services.openai_provider import OpenAIProvider

        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


ai_provider = get_ai_provider()
