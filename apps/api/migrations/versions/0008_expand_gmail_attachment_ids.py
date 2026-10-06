"""Allow Google attachment identifiers longer than 255 characters.

Revision ID: 0008_expand_gmail_attachment_ids
Revises: 0007_evaluation_tracking
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_expand_gmail_attachment_ids"
down_revision: str | Sequence[str] | None = "0007_evaluation_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "attachments",
        "provider_attachment_id",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "attachments",
        "provider_attachment_id",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
