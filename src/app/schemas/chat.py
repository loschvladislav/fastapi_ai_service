from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(description="The content of the message", min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        description="List of messages in the conversation",
        min_length=1,
        max_length=50,
    )
    model: str = Field(
        default="gpt-3.5-turbo",
        description="The OpenAI model to use",
    )
    max_tokens: int = Field(
        default=1000,
        ge=1,
        le=4000,
        description="Maximum tokens in the response",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0=deterministic, 2=creative)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "What is Python?"},
                    ],
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 500,
                    "temperature": 0.7,
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    message: ChatMessage = Field(description="The assistant's response")
    model: str = Field(description="The model used for the response")
    usage: dict = Field(description="Token usage statistics")
