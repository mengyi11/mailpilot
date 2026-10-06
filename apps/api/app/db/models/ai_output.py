from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EmailAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_analyses"
    __table_args__ = (Index("ix_email_analyses_email_created", "email_id", "created_at"),)

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(16))
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[str | None] = mapped_column(String(32))
    action_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    extracted_dates: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    structured_output: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))


class Translation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "translations"
    __table_args__ = (Index("ix_translations_email_created", "email_id", "created_at"),)

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("email_analyses.id", ondelete="SET NULL")
    )
    source_language: Mapped[str | None] = mapped_column(String(16))
    target_language: Mapped[str] = mapped_column(String(16), nullable=False)
    translated_subject: Mapped[str | None] = mapped_column(Text)
    translated_body: Mapped[str] = mapped_column(Text, nullable=False)
    translated_html: Mapped[str | None] = mapped_column(Text)
    ocr_blocks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    model_name: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)


class ReplyDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reply_drafts"
    __table_args__ = (Index("ix_reply_drafts_email_created", "email_id", "created_at"),)

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("email_analyses.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    tone: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(16))
    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    generation_context: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
