from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(
        description="The text to summarize",
        min_length=10,
        max_length=50000,
    )
    max_length: int = Field(
        default=200,
        ge=50,
        le=1000,
        description="Maximum length of the summary in words",
    )
    style: str = Field(
        default="concise",
        description="Summary style: concise, detailed, or bullet_points",
        pattern="^(concise|detailed|bullet_points)$",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Python is a high-level programming language...",
                    "max_length": 100,
                    "style": "concise",
                }
            ]
        }
    }


class SummarizeResponse(BaseModel):
    summary: str = Field(description="The summarized text")
    original_length: int = Field(description="Character count of original text")
    summary_length: int = Field(description="Character count of summary")
    model: str = Field(description="The model used for summarization")
    usage: dict = Field(description="Token usage statistics")
