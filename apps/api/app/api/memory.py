from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.models.agent import AgentRun, AgentStep, Approval, ToolCall
from app.db.models.identity import EmailAccount
from app.db.models.productivity import Memory
from app.db.session import get_db
from app.schemas.memory import (
    EpisodicMemoryCreate,
    EpisodicMemoryResponse,
    EpisodicMemoryUpdate,
    ReplyPreviewRequest,
    ReplyPreviewResponse,
    SessionRunResponse,
    UserPreferencesResponse,
    UserPreferencesToolResponse,
    UserPreferencesUpdate,
)
from app.services.memory import (
    create_episode,
    create_reply_preview,
    episode_response,
    get_or_create_preferences,
    get_user_preferences_tool,
    preference_payload,
    preference_response,
    update_preferences,
)


router = APIRouter(prefix="/memory", tags=["memory"])


def current_user_id(db: Session) -> UUID:
    user_id = db.scalar(
        select(EmailAccount.user_id)
        .where(
            EmailAccount.provider == "google",
            EmailAccount.sync_status.in_(["connected", "syncing", "error"]),
        )
        .order_by(EmailAccount.updated_at.desc())
        .limit(1)
    )
    if user_id is None:
        raise AppError(
            code="ACCOUNT_NOT_CONNECTED",
            message="Connect a Gmail account before using Memory.",
            status_code=409,
        )
    return user_id


@router.get("/preferences", response_model=UserPreferencesResponse)
def read_preferences(db: Session = Depends(get_db)) -> UserPreferencesResponse:
    preference = get_or_create_preferences(db, current_user_id(db))
    db.commit()
    return preference_response(preference)


@router.put("/preferences", response_model=UserPreferencesResponse)
def write_preferences(
    data: UserPreferencesUpdate, db: Session = Depends(get_db)
) -> UserPreferencesResponse:
    preference = update_preferences(db, current_user_id(db), data)
    db.commit()
    db.refresh(preference)
    return preference_response(preference)


@router.get("/items", response_model=list[EpisodicMemoryResponse])
def list_memory_items(
    include_inactive: bool = True, db: Session = Depends(get_db)
) -> list[EpisodicMemoryResponse]:
    query = select(Memory).where(
        Memory.user_id == current_user_id(db),
        Memory.scope == "episodic",
        Memory.kind == "suggestion_feedback",
    )
    if not include_inactive:
        query = query.where(Memory.is_active.is_(True))
    rows = db.scalars(query.order_by(Memory.created_at.desc())).all()
    return [episode_response(row) for row in rows]


@router.post("/items", response_model=EpisodicMemoryResponse, status_code=201)
def add_memory_item(
    data: EpisodicMemoryCreate, db: Session = Depends(get_db)
) -> EpisodicMemoryResponse:
    memory = create_episode(db, current_user_id(db), data)
    db.commit()
    db.refresh(memory)
    return episode_response(memory)


def owned_memory(db: Session, memory_id: UUID) -> Memory:
    memory = db.scalar(
        select(Memory).where(
            Memory.id == memory_id,
            Memory.user_id == current_user_id(db),
            Memory.scope == "episodic",
        )
    )
    if memory is None:
        raise AppError(code="MEMORY_NOT_FOUND", message="Memory was not found.", status_code=404)
    return memory


@router.patch("/items/{memory_id}", response_model=EpisodicMemoryResponse)
def edit_memory_item(
    memory_id: UUID, data: EpisodicMemoryUpdate, db: Session = Depends(get_db)
) -> EpisodicMemoryResponse:
    memory = owned_memory(db, memory_id)
    if data.summary is not None:
        memory.content = {**memory.content, "summary": data.summary, "is_email_fact": False}
    if data.is_active is not None:
        memory.is_active = data.is_active
    db.commit()
    db.refresh(memory)
    return episode_response(memory)


@router.delete("/items/{memory_id}", status_code=204)
def delete_memory_item(memory_id: UUID, db: Session = Depends(get_db)) -> Response:
    db.delete(owned_memory(db, memory_id))
    db.commit()
    return Response(status_code=204)


@router.post("/reply-preview", response_model=ReplyPreviewResponse)
def preview_reply(
    data: ReplyPreviewRequest, db: Session = Depends(get_db)
) -> ReplyPreviewResponse:
    preference = get_or_create_preferences(db, current_user_id(db))
    db.commit()
    return create_reply_preview(preference_payload(preference), data.recipient_name, data.purpose)


@router.get("/session-runs", response_model=list[SessionRunResponse])
def list_session_runs(db: Session = Depends(get_db)) -> list[SessionRunResponse]:
    user_id = current_user_id(db)
    rows = db.execute(
        select(
            AgentRun,
            func.count(func.distinct(AgentStep.id)),
            func.count(func.distinct(ToolCall.id)),
            func.count(func.distinct(Approval.id)),
        )
        .outerjoin(AgentStep, AgentStep.agent_run_id == AgentRun.id)
        .outerjoin(ToolCall, ToolCall.agent_run_id == AgentRun.id)
        .outerjoin(Approval, Approval.agent_run_id == AgentRun.id)
        .where(AgentRun.user_id == user_id)
        .group_by(AgentRun.id)
        .order_by(AgentRun.created_at.desc())
        .limit(20)
    ).all()
    return [
        SessionRunResponse(
            id=run.id,
            workflow_name=run.workflow_name,
            status=run.status,
            trace_id=run.trace_id,
            email_id=run.email_id,
            steps=steps,
            tool_calls=tools,
            approvals=approvals,
            created_at=run.created_at,
        )
        for run, steps, tools, approvals in rows
    ]


def verify_memory_tool_key(
    x_memory_tool_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.memory_tool_api_key and x_memory_tool_key != settings.memory_tool_api_key:
        raise AppError(
            code="MEMORY_TOOL_UNAUTHORIZED",
            message="The Memory tool credential is invalid.",
            status_code=401,
        )


@router.get(
    "/tools/users/{user_id}/preferences",
    response_model=UserPreferencesToolResponse,
    dependencies=[Depends(verify_memory_tool_key)],
)
def read_preferences_tool(
    user_id: UUID, db: Session = Depends(get_db)
) -> UserPreferencesToolResponse:
    result = get_user_preferences_tool(db, user_id)
    db.commit()
    return result
