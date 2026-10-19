from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ToolModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: value.split("_")[0]
        + "".join(part.capitalize() for part in value.split("_")[1:]),
        populate_by_name=True,
    )


class ToolExecuteRequest(ToolModel):
    user_id: UUID
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=200)
    trace_id: str | None = Field(default=None, max_length=64)


class ToolError(ToolModel):
    code: str
    message: str
    retryable: bool = False


class ToolResult(ToolModel):
    ok: bool
    tool: str
    data: dict[str, Any] | list[Any] | None = None
    error: ToolError | None = None
    cached: bool = False
    tool_call_id: UUID | None = None
    trace_id: str
    duration_ms: float


class ToolDefinition(ToolModel):
    name: str
    description: str
    permission: str
    input_schema: dict[str, Any]
