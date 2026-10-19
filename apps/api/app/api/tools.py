from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.schemas.tool import ToolDefinition, ToolExecuteRequest, ToolResult
from app.tools import TOOL_REGISTRY


router = APIRouter(prefix="/tools", tags=["agent-tools"])


def verify_dify_tool_key(
    x_tool_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.dify_tool_api_key or x_tool_api_key != settings.dify_tool_api_key:
        raise AppError(
            code="TOOL_API_UNAUTHORIZED",
            message="The Tool API credential is missing or invalid.",
            status_code=401,
        )


@router.get(
    "",
    response_model=list[ToolDefinition],
    dependencies=[Depends(verify_dify_tool_key)],
    summary="List tools exposed to Dify",
)
def list_tools() -> list[ToolDefinition]:
    return [ToolDefinition.model_validate(item) for item in TOOL_REGISTRY.definitions()]


@router.post(
    "/{tool_name}/execute",
    response_model=ToolResult,
    dependencies=[Depends(verify_dify_tool_key)],
    summary="Execute one registered tool",
)
async def execute_tool(
    tool_name: str,
    request: ToolExecuteRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ToolResult:
    return await TOOL_REGISTRY.execute(
        db,
        name=tool_name,
        user_id=request.user_id,
        arguments=request.arguments,
        permissions=frozenset(settings.dify_tool_permissions),
        idempotency_key=request.idempotency_key,
        trace_id=request.trace_id,
        timeout_seconds=settings.tool_timeout_seconds,
    )


def _fixed_tool_endpoint(tool_name: str):
    async def endpoint(
        request: ToolExecuteRequest,
        db: Session = Depends(get_db),
        settings: Settings = Depends(get_settings),
    ) -> ToolResult:
        return await TOOL_REGISTRY.execute(
            db,
            name=tool_name,
            user_id=request.user_id,
            arguments=request.arguments,
            permissions=frozenset(settings.dify_tool_permissions),
            idempotency_key=request.idempotency_key,
            trace_id=request.trace_id,
            timeout_seconds=settings.tool_timeout_seconds,
        )

    endpoint.__name__ = f"execute_{tool_name}"
    return endpoint


# Fixed paths and operation IDs make every capability appear as a separate
# selectable Tool when Dify imports FastAPI's OpenAPI document.
for definition in TOOL_REGISTRY.definitions():
    name = definition["name"]
    router.add_api_route(
        f"/{name}",
        _fixed_tool_endpoint(name),
        methods=["POST"],
        response_model=ToolResult,
        dependencies=[Depends(verify_dify_tool_key)],
        summary=definition["description"],
        operation_id=name,
    )
