from datetime import datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EmailThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_threads"
    __table_args__ = (
        UniqueConstraint(
            "email_account_id",
            "provider_thread_id",
            name="uq_email_threads_account_provider_id",
        ),
        Index("ix_email_threads_account_latest", "email_account_id", "latest_message_at"),
    )

    email_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False
    )
    provider_thread_id: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    participants: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    latest_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    emails: Mapped[list["Email"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )


class Email(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "emails"
    __table_args__ = (
        UniqueConstraint(
            "email_account_id",
            "provider_message_id",
            name="uq_emails_account_provider_id",
        ),
        Index("ix_emails_account_received", "email_account_id", "received_at"),
        Index("ix_emails_thread_received", "thread_id", "received_at"),
    )

    email_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False
    )
    thread_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("email_threads.id", ondelete="SET NULL")
    )
    provider_message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    internet_message_id: Mapped[str | None] = mapped_column(String(998))
    sender: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    recipients: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    subject: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    labels: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    thread: Mapped[EmailThread | None] = relationship(back_populates="emails")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["EmailChunk"]] = relationship(
        back_populates="email", cascade="all, delete-orphan"
    )


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        UniqueConstraint(
            "email_id",
            "provider_attachment_id",
            name="uq_attachments_email_provider_id",
        ),
        Index("ix_attachments_email_id", "email_id"),
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    provider_attachment_id: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    storage_key: Mapped[str | None] = mapped_column(Text)
    content_id: Mapped[str | None] = mapped_column(String(998))
    is_inline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    email: Mapped[Email] = relationship(back_populates="attachments")


class EmailChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_chunks"
    __table_args__ = (
        UniqueConstraint("email_id", "chunk_index", name="uq_email_chunks_position"),
        Index("ix_email_chunks_email_id", "email_id"),
        Index(
            "ix_email_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    email: Mapped[Email] = relationship(back_populates="chunks")
