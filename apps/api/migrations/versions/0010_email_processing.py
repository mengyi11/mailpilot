"""Add normalized AI input and attachment extraction fields.

Revision ID: 0010_email_processing
Revises: 0009_rich_email_translations
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0010_email_processing"
down_revision: str | Sequence[str] | None = "0009_rich_email_translations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("emails", sa.Column("raw_body_html", sa.Text()))
    op.add_column("emails", sa.Column("cleaned_text", sa.Text()))
    op.add_column("emails", sa.Column("original_timezone", sa.String(length=64)))
    op.add_column(
        "emails",
        sa.Column(
            "user_timezone",
            sa.String(length=64),
            server_default="UTC",
            nullable=False,
        ),
    )
    op.add_column("emails", sa.Column("reference_date", sa.String(length=10)))
    op.add_column(
        "emails",
        sa.Column(
            "processing_metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "attachments",
        sa.Column(
            "extraction_status",
            sa.String(length=32),
            server_default="metadata_only",
            nullable=False,
        ),
    )
    op.add_column("attachments", sa.Column("extracted_text", sa.Text()))
    op.add_column("attachments", sa.Column("extraction_error", sa.Text()))


def downgrade() -> None:
    op.drop_column("attachments", "extraction_error")
    op.drop_column("attachments", "extracted_text")
    op.drop_column("attachments", "extraction_status")
    op.drop_column("emails", "processing_metadata")
    op.drop_column("emails", "reference_date")
    op.drop_column("emails", "user_timezone")
    op.drop_column("emails", "original_timezone")
    op.drop_column("emails", "cleaned_text")
    op.drop_column("emails", "raw_body_html")
