"""Create benchmark cases, evaluation runs, and evaluation results.

Revision ID: 0007_evaluation_tracking
Revises: 0006_agent_audit_approvals
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0007_evaluation_tracking"
down_revision: str | Sequence[str] | None = "0006_agent_audit_approvals"
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
        "benchmark_cases",
        sa.Column("suite_name", sa.String(length=128), nullable=False),
        sa.Column("case_key", sa.String(length=128), nullable=False),
        sa.Column("dataset_split", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_data", postgresql.JSONB(), nullable=False),
        sa.Column("expected_output", postgresql.JSONB(), nullable=False),
        sa.Column("scoring_config", postgresql.JSONB(), nullable=False),
        sa.Column("tags", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_key"),
    )
    op.create_index(
        "ix_benchmark_cases_suite_split",
        "benchmark_cases",
        ["suite_name", "dataset_split"],
    )
    op.create_table(
        "evaluation_runs",
        sa.Column("suite_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("workflow_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("git_commit_sha", sa.String(length=64), nullable=True),
        sa.Column("run_config", postgresql.JSONB(), nullable=False),
        sa.Column("aggregate_metrics", postgresql.JSONB(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_evaluation_runs_suite_created", "evaluation_runs", ["suite_name", "created_at"]
    )
    op.create_table(
        "evaluation_results",
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("benchmark_case_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("actual_output", postgresql.JSONB(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["benchmark_case_id"], ["benchmark_cases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evaluation_run_id",
            "benchmark_case_id",
            name="uq_evaluation_results_run_case",
        ),
    )
    op.create_index(
        "ix_evaluation_results_run_passed",
        "evaluation_results",
        ["evaluation_run_id", "passed"],
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_run_passed", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_evaluation_runs_suite_created", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index("ix_benchmark_cases_suite_split", table_name="benchmark_cases")
    op.drop_table("benchmark_cases")
