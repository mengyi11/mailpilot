from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    email_accounts: Mapped[list["EmailAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmailAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_account_id", name="uq_email_accounts_provider_id"
        ),
        Index("ix_email_accounts_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email_address: Mapped[str] = mapped_column(String(320), nullable=False)
    sync_status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    provider_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="email_accounts")
    oauth_credential: Mapped["OAuthCredential | None"] = relationship(
        back_populates="email_account",
        cascade="all, delete-orphan",
        uselist=False,
    )


class OAuthCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "oauth_credentials"

    email_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    access_token_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_ciphertext: Mapped[str | None] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    token_type: Mapped[str | None] = mapped_column(String(32))
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    key_version: Mapped[str] = mapped_column(String(64), nullable=False)

    email_account: Mapped[EmailAccount] = relationship(
        back_populates="oauth_credential"
    )
