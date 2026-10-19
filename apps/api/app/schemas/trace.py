from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class TraceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TraceStepResponse(TraceBase):
    id: UUID; sequence: int; name: str; step_type: str; status: str
    model_name: str | None = None; prompt_version: str | None = None
    input_tokens: int | None = None; output_tokens: int | None = None
    cost_usd: Decimal | None = None; duration_ms: int | None = None; retry_count: int = 0
    input_data: dict[str, Any] = {}; output_data: dict[str, Any] = {}
    error_message: str | None = None; started_at: datetime | None = None; completed_at: datetime | None = None

class TraceToolResponse(TraceBase):
    id: UUID; tool_name: str; status: str; request_arguments: dict[str, Any] = {}; response_data: dict[str, Any] = {}
    duration_ms: int | None = None; retry_count: int = 0; verified_at: datetime | None = None
    error_message: str | None = None; started_at: datetime | None = None; completed_at: datetime | None = None

class TraceApprovalResponse(TraceBase):
    id: UUID; action: str; resource_type: str; resource_id: UUID | None = None; payload_hash: str | None = None
    status: str; requested_at: datetime; decided_at: datetime | None = None; expires_at: datetime | None = None
    executed_at: datetime | None = None; verification_result: dict[str, Any] = {}

class AgentTraceResponse(TraceBase):
    id: UUID; trace_id: str; email_id: UUID | None = None; user_goal: str | None = None
    workflow_name: str; workflow_version: str; prompt_version: str | None = None; model_name: str | None = None
    status: str; input_tokens: int | None = None; output_tokens: int | None = None; cost_usd: Decimal | None = None
    duration_ms: int | None = None; retry_count: int = 0; token_budget: int | None = None
    input_data: dict[str, Any] = {}; output_data: dict[str, Any] = {}; error_code: str | None = None
    error_message: str | None = None; created_at: datetime; started_at: datetime | None = None; completed_at: datetime | None = None
    steps: list[TraceStepResponse] = []; tools: list[TraceToolResponse] = []; approvals: list[TraceApprovalResponse] = []

class TraceOverviewResponse(BaseModel):
    runs: int; total_tokens: int; total_cost_usd: Decimal; avg_latency_ms: float; failed_runs: int

