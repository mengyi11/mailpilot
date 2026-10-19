"""Add agent trace timing, token, cost, and budget fields.

Revision ID: 0012_agent_observability
Revises: 0011_calendar_approval
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0012_agent_observability"
down_revision: str | Sequence[str] | None = "0011_calendar_approval"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("prompt_version", sa.String(length=64)))
    op.add_column("agent_runs", sa.Column("user_goal", sa.Text()))
    op.add_column("agent_runs", sa.Column("duration_ms", sa.Integer()))
    op.add_column("agent_runs", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("agent_runs", sa.Column("token_budget", sa.Integer()))
    op.add_column("agent_steps", sa.Column("model_name", sa.String(length=128)))
    op.add_column("agent_steps", sa.Column("prompt_version", sa.String(length=64)))
    op.add_column("agent_steps", sa.Column("input_tokens", sa.Integer()))
    op.add_column("agent_steps", sa.Column("output_tokens", sa.Integer()))
    op.add_column("agent_steps", sa.Column("cost_usd", sa.Numeric(12, 6)))
    op.add_column("agent_steps", sa.Column("duration_ms", sa.Integer()))
    op.add_column("tool_calls", sa.Column("duration_ms", sa.Integer()))


def downgrade() -> None:
    op.drop_column("tool_calls", "duration_ms")
    op.drop_column("agent_steps", "duration_ms")
    op.drop_column("agent_steps", "cost_usd")
    op.drop_column("agent_steps", "output_tokens")
    op.drop_column("agent_steps", "input_tokens")
    op.drop_column("agent_steps", "prompt_version")
    op.drop_column("agent_steps", "model_name")
    op.drop_column("agent_runs", "token_budget")
    op.drop_column("agent_runs", "retry_count")
    op.drop_column("agent_runs", "duration_ms")
    op.drop_column("agent_runs", "user_goal")
    op.drop_column("agent_runs", "prompt_version")
