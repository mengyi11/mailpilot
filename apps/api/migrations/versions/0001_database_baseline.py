"""Establish the MailPilot database migration baseline.

Revision ID: 0001_database_baseline
Revises:
"""

from collections.abc import Sequence


revision: str = "0001_database_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Mark the initial database schema baseline."""


def downgrade() -> None:
    """Return to the state before migration tracking."""
