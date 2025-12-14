from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(
        description="The text to translate",
        min_length=1,
        max_length=10000,
    )
    source_language: str = Field(
        default="auto",
        description="Source language (use 'auto' for auto-detection)",
        max_length=50,
    )
    target_language: str = Field(
        description="Target language for translation",
        min_length=2,
        max_length=50,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Hello, how are you?",
                    "source_language": "English",
                    "target_language": "Spanish",
                }
            ]
        }
    }


class TranslateResponse(BaseModel):
    translated_text: str = Field(description="The translated text")
    source_language: str = Field(description="Detected or specified source language")
    target_language: str = Field(description="Target language")
    model: str = Field(description="The model used for translation")
    usage: dict = Field(description="Token usage statistics")
