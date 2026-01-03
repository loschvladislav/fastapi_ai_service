import uuid
from datetime import datetime

from pydantic import BaseModel


class UsageRecordResponse(BaseModel):
    id: uuid.UUID
    endpoint: str
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    period_start: datetime
    period_end: datetime
