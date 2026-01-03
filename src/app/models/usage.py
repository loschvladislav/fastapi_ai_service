import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    api_key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    api_key: Mapped["APIKey"] = relationship(
        "APIKey",
        back_populates="usage_records",
    )

    def __repr__(self) -> str:
        return f"<UsageRecord {self.endpoint} tokens={self.tokens_used}>"


# Import at the end to avoid circular imports
from app.models.api_key import APIKey  # noqa: E402, F401
