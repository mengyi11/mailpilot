"""Add immutable approval and calendar verification audit fields.

Revision ID: 0011_calendar_approval
Revises: 0010_email_processing
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0011_calendar_approval"
down_revision: str | Sequence[str] | None = "0010_email_processing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("approvals", sa.Column("payload_hash", sa.String(length=64)))
    op.add_column("approvals", sa.Column("executed_at", sa.DateTime(timezone=True)))
    op.add_column(
        "approvals",
        sa.Column(
            "verification_result",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("approvals", "verification_result")
    op.drop_column("approvals", "executed_at")
    op.drop_column("approvals", "payload_hash")
