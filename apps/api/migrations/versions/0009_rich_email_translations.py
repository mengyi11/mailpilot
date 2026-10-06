"""Store layout-preserving HTML translations and image OCR results.

Revision ID: 0009_rich_email_translations
Revises: 0008_expand_gmail_attachment_ids
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0009_rich_email_translations"
down_revision: str | Sequence[str] | None = "0008_expand_gmail_attachment_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("translations", sa.Column("translated_html", sa.Text()))
    op.add_column(
        "translations",
        sa.Column(
            "ocr_blocks",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("translations", "ocr_blocks")
    op.drop_column("translations", "translated_html")
