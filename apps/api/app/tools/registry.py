from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.agent import AgentRun, ToolCall
from app.schemas.tool import ToolError, ToolResult
from app.tools.base import BaseTool, ToolContext, ToolExecutionError
from app.tools.implementations import TOOLS


logger = logging.getLogger("mailpilot.tools")


class ToolRegistry:
    def __init__(self, tools: list[BaseTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}
        if len(self._tools) != len(tools):
            raise ValueError("Tool names must be unique")

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def definitions(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "permission": tool.permission,
                "input_schema": tool.input_model.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    async def execute(
        self,
        db: Session,
        *,
        name: str,
        user_id,
        arguments: dict,
        permissions: frozenset[str],
        idempotency_key: str,
        trace_id: str | None,
        timeout_seconds: float,
    ) -> ToolResult:
        started = perf_counter()
        trace = trace_id or uuid4().hex
        tool = self.get(name)
        if tool is None:
            return self._error(name, trace, started, "TOOL_NOT_FOUND", "Unknown tool.")
        stored_key = hashlib.sha256(f"{user_id}:{name}:{idempotency_key}".encode()).hexdigest()
        cached = db.execute(
            select(ToolCall, AgentRun)
            .join(AgentRun, ToolCall.agent_run_id == AgentRun.id)
            .where(ToolCall.idempotency_key == stored_key, AgentRun.user_id == user_id, ToolCall.status == "completed")
        ).one_or_none()
        if cached:
            call, run = cached
            return ToolResult(ok=True, tool=name, data=call.response_data, cached=True, tool_call_id=call.id, trace_id=run.trace_id, duration_ms=round((perf_counter() - started) * 1000, 2))

        run = AgentRun(user_id=user_id, workflow_name=f"tool:{name}", workflow_version="v1", status="running", trace_id=trace, input_data={"tool": name}, started_at=datetime.now(UTC))
        db.add(run)
        db.flush()
        call = ToolCall(agent_run_id=run.id, tool_name=name, status="running", request_arguments=arguments, idempotency_key=stored_key, started_at=datetime.now(UTC))
        db.add(call)
        db.flush()
        try:
            context = ToolContext(user_id=user_id, permissions=permissions, trace_id=trace)
            tool.authorize(context)
            parsed = tool.parse_input(arguments)
            # A failed Tool must not leave a half-created task or draft. The
            # nested transaction rolls back business writes while preserving
            # the outer Run/ToolCall audit record.
            with db.begin_nested():
                data = await asyncio.wait_for(
                    tool.execute(db, context, parsed), timeout=timeout_seconds
                )
            completed = datetime.now(UTC)
            call.status, call.response_data, call.verified_at, call.completed_at = "completed", data, completed, completed
            run.status, run.output_data, run.completed_at = "completed", {"tool_call_id": str(call.id)}, completed
            db.commit()
            logger.info("tool_completed", extra={"tool": name, "trace_id": trace, "user_id": str(user_id)})
            return ToolResult(ok=True, tool=name, data=data, tool_call_id=call.id, trace_id=trace, duration_ms=round((perf_counter() - started) * 1000, 2))
        except asyncio.TimeoutError:
            error = ToolExecutionError("TOOL_TIMEOUT", f"{name} exceeded its timeout.", retryable=True)
        except ValidationError as exc:
            error = ToolExecutionError("TOOL_INPUT_INVALID", str(exc))
        except ToolExecutionError as exc:
            error = exc
        except Exception:
            logger.exception("tool_failed", extra={"tool": name, "trace_id": trace})
            error = ToolExecutionError("TOOL_EXECUTION_FAILED", "The tool could not complete.", retryable=True)
        failed = datetime.now(UTC)
        call.status, call.error_message, call.completed_at = "failed", error.message, failed
        run.status, run.error_code, run.error_message, run.completed_at = "failed", error.code, error.message, failed
        db.commit()
        return self._error(name, trace, started, error.code, error.message, error.retryable, call.id)

    @staticmethod
    def _error(name, trace, started, code, message, retryable=False, call_id=None):
        return ToolResult(ok=False, tool=name, error=ToolError(code=code, message=message, retryable=retryable), tool_call_id=call_id, trace_id=trace, duration_ms=round((perf_counter() - started) * 1000, 2))


TOOL_REGISTRY = ToolRegistry(TOOLS)
