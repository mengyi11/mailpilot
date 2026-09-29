"""Create email threads, messages, attachments, and vector chunks.

Revision ID: 0003_email_storage
Revises: 0002_identity_and_oauth
"""

from collections.abc import Sequence

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003_email_storage"
down_revision: str | Sequence[str] | None = "0002_identity_and_oauth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_threads",
        sa.Column("email_account_id", sa.Uuid(), nullable=False),
        sa.Column("provider_thread_id", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("participants", postgresql.JSONB(), nullable=False),
        sa.Column("latest_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["email_account_id"], ["email_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_account_id",
            "provider_thread_id",
            name="uq_email_threads_account_provider_id",
        ),
    )
    op.create_index(
        "ix_email_threads_account_latest",
        "email_threads",
        ["email_account_id", "latest_message_at"],
    )
    op.create_table(
        "emails",
        sa.Column("email_account_id", sa.Uuid(), nullable=False),
        sa.Column("thread_id", sa.Uuid(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=False),
        sa.Column("internet_message_id", sa.String(length=998), nullable=True),
        sa.Column("sender", postgresql.JSONB(), nullable=False),
        sa.Column("recipients", postgresql.JSONB(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("labels", postgresql.JSONB(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("is_starred", sa.Boolean(), nullable=False),
        sa.Column("raw_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["email_account_id"], ["email_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["email_threads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_account_id",
            "provider_message_id",
            name="uq_emails_account_provider_id",
        ),
    )
    op.create_index("ix_emails_account_received", "emails", ["email_account_id", "received_at"])
    op.create_index("ix_emails_thread_received", "emails", ["thread_id", "received_at"])
    op.create_table(
        "attachments",
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("provider_attachment_id", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("content_id", sa.String(length=998), nullable=True),
        sa.Column("is_inline", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_id", "provider_attachment_id", name="uq_attachments_email_provider_id"
        ),
    )
    op.create_index("ix_attachments_email_id", "attachments", ["email_id"])
    op.create_table(
        "email_chunks",
        sa.Column("email_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("chunk_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_id", "chunk_index", name="uq_email_chunks_position"),
    )
    op.create_index("ix_email_chunks_email_id", "email_chunks", ["email_id"])
    op.create_index(
        "ix_email_chunks_embedding_hnsw",
        "email_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_email_chunks_embedding_hnsw", table_name="email_chunks", postgresql_using="hnsw")
    op.drop_index("ix_email_chunks_email_id", table_name="email_chunks")
    op.drop_table("email_chunks")
    op.drop_index("ix_attachments_email_id", table_name="attachments")
    op.drop_table("attachments")
    op.drop_index("ix_emails_thread_received", table_name="emails")
    op.drop_index("ix_emails_account_received", table_name="emails")
    op.drop_table("emails")
    op.drop_index("ix_email_threads_account_latest", table_name="email_threads")
    op.drop_table("email_threads")
