"""Create email analyses, translations, and reply drafts.

Revision ID: 0004_ai_outputs
Revises: 0003_email_storage
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_ai_outputs"
down_revision: str | Sequence[str] | None = "0003_email_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "email_analyses",
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("model_provider", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("detected_language", sa.String(length=16), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=True),
        sa.Column("action_items", postgresql.JSONB(), nullable=False),
        sa.Column("extracted_dates", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("structured_output", postgresql.JSONB(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_analyses_email_created", "email_analyses", ["email_id", "created_at"]
    )
    op.create_table(
        "translations",
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=True),
        sa.Column("source_language", sa.String(length=16), nullable=True),
        sa.Column("target_language", sa.String(length=16), nullable=False),
        sa.Column("translated_subject", sa.Text(), nullable=True),
        sa.Column("translated_body", sa.Text(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["analysis_id"], ["email_analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_translations_email_created", "translations", ["email_id", "created_at"])
    op.create_table(
        "reply_drafts",
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("tone", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("generation_context", postgresql.JSONB(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["analysis_id"], ["email_analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reply_drafts_email_created", "reply_drafts", ["email_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_reply_drafts_email_created", table_name="reply_drafts")
    op.drop_table("reply_drafts")
    op.drop_index("ix_translations_email_created", table_name="translations")
    op.drop_table("translations")
    op.drop_index("ix_email_analyses_email_created", table_name="email_analyses")
    op.drop_table("email_analyses")
