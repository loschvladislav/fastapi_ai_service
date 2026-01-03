import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    usage_records: Mapped[list["UsageRecord"]] = relationship(
        "UsageRecord",
        back_populates="api_key",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<APIKey {self.name} ({self.key_prefix}...)>"

    @staticmethod
    def generate_key() -> str:
        """Generate a new API key with 'ai_' prefix."""
        return f"ai_{secrets.token_urlsafe(32)}"


# Import at the end to avoid circular imports
from app.models.usage import UsageRecord  # noqa: E402, F401
