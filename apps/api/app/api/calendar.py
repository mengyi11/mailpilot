from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models.agent import Approval
from app.db.models.identity import EmailAccount
from app.db.models.productivity import CalendarDraft
from app.db.session import get_db
from app.api.memory import current_user_id
from app.schemas.calendar import (
    CalendarEventInput,
    CalendarEventResponse,
    CalendarEventUpdate,
    CalendarOverviewResponse,
    ApprovalDecisionRequest,
    CalendarAvailabilityInput,
    CalendarAvailabilityResponse,
)
from app.schemas.memory import EpisodicMemoryCreate
from app.services.memory import create_episode
from app.services.approval import (
    calendar_payload,
    canonical_payload_hash,
    new_calendar_approval,
)
from app.services.google_calendar import GoogleCalendarService
from app.core.config import get_settings
from app.tools import TOOL_REGISTRY


router = APIRouter(prefix="/calendar", tags=["calendar"])


def event_response(
    item: CalendarDraft, approval: Approval | None = None
) -> CalendarEventResponse:
    source = "manual" if item.source_evidence.get("source") == "manual" else "email"
    return CalendarEventResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        timezone=item.timezone,
        location=item.location,
        attendees=[entry.get("email", "") for entry in item.attendees],
        status=item.status,
        source=source,
        email_id=item.email_id,
        evidence=item.source_evidence.get("text"),
        created_at=item.created_at,
        approval_id=approval.id if approval else None,
        approval_payload_hash=approval.payload_hash if approval else None,
        approval_expires_at=approval.expires_at if approval else None,
        provider_event_id=item.provider_event_id,
        verified=bool(
            approval
            and approval.verification_result.get("verified")
            and item.provider_event_id
        ),
    )


def owned_item(db: Session, user_id: UUID, item_id: UUID) -> CalendarDraft:
    item = db.scalar(
        select(CalendarDraft).where(
            CalendarDraft.id == item_id,
            CalendarDraft.user_id == user_id,
        )
    )
    if item is None:
        raise AppError(
            code="CALENDAR_ITEM_NOT_FOUND",
            message="Calendar item was not found.",
            status_code=404,
        )
    return item


@router.get("", response_model=CalendarOverviewResponse)
def calendar_overview(
    starts_from: datetime | None = Query(default=None),
    starts_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CalendarOverviewResponse:
    user_id = current_user_id(db)
    statement = select(CalendarDraft).where(CalendarDraft.user_id == user_id)
    if starts_from:
        statement = statement.where(CalendarDraft.starts_at >= starts_from)
    if starts_before:
        statement = statement.where(CalendarDraft.starts_at < starts_before)
    items = db.scalars(statement.order_by(CalendarDraft.starts_at)).all()
    approvals = {
        approval.resource_id: approval
        for approval in db.scalars(
            select(Approval).where(
                Approval.user_id == user_id,
                Approval.resource_type == "calendar_draft",
                Approval.resource_id.in_([item.id for item in items]),
            )
        ).all()
    } if items else {}
    return CalendarOverviewResponse(
        events=[
            event_response(item, approvals.get(item.id))
            for item in items
            if item.status == "confirmed"
        ],
        candidates=[
            event_response(item, approvals.get(item.id))
            for item in items
            if item.status in {"pending_approval", "needs_clarification", "verification_failed"}
        ],
    )


@router.post("/events", response_model=CalendarEventResponse, status_code=201)
def create_manual_event(
    data: CalendarEventInput,
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    item = CalendarDraft(
        user_id=current_user_id(db),
        status="confirmed",
        title=data.title,
        description=data.description,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        timezone=data.timezone,
        location=data.location,
        attendees=[{"email": email} for email in data.attendees],
        source_evidence={"source": "manual"},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return event_response(item)


@router.get("/candidates/{item_id}", response_model=CalendarEventResponse)
def get_calendar_candidate(
    item_id: UUID, db: Session = Depends(get_db)
) -> CalendarEventResponse:
    user_id = current_user_id(db)
    item = owned_item(db, user_id, item_id)
    approval = pending_approval(db, user_id, item.id)
    return event_response(item, approval)


@router.patch("/events/{item_id}", response_model=CalendarEventResponse)
def update_event(
    item_id: UUID,
    data: CalendarEventUpdate,
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    item = owned_item(db, current_user_id(db), item_id)
    if item.status != "confirmed":
        raise AppError(
            code="CALENDAR_EVENT_NOT_CONFIRMED",
            message="Only confirmed calendar events can be edited.",
            status_code=409,
        )
    updates = data.model_dump(exclude_unset=True)
    starts_at = updates.get("starts_at", item.starts_at)
    ends_at = updates.get("ends_at", item.ends_at)
    if ends_at is not None and ends_at <= starts_at:
        raise AppError(
            code="CALENDAR_TIME_RANGE_INVALID",
            message="Event end must be later than its start.",
            status_code=422,
        )
    for field, value in updates.items():
        setattr(
            item,
            field,
            [{"email": email} for email in value]
            if field == "attendees" and value is not None
            else value,
        )
    db.commit()
    db.refresh(item)
    return event_response(item)


@router.delete("/events/{item_id}", status_code=204)
def delete_event(item_id: UUID, db: Session = Depends(get_db)) -> Response:
    item = owned_item(db, current_user_id(db), item_id)
    if item.status != "confirmed":
        raise AppError(
            code="CALENDAR_EVENT_NOT_CONFIRMED",
            message="Only confirmed calendar events can be deleted here.",
            status_code=409,
        )
    db.delete(item)
    db.commit()
    return Response(status_code=204)


def google_account(db: Session, user_id: UUID) -> EmailAccount:
    account = db.scalar(
        select(EmailAccount).where(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == "google",
            EmailAccount.sync_status == "connected",
        )
    )
    if account is None:
        raise AppError(
            code="GOOGLE_CALENDAR_NOT_CONNECTED",
            message="请先连接 Google 账户。",
            status_code=409,
        )
    return account


def pending_approval(db: Session, user_id: UUID, item_id: UUID) -> Approval:
    approval = db.scalar(
        select(Approval)
        .where(
            Approval.user_id == user_id,
            Approval.resource_type == "calendar_draft",
            Approval.resource_id == item_id,
        )
        .order_by(Approval.requested_at.desc())
    )
    if approval is None:
        raise AppError(
            code="APPROVAL_NOT_FOUND",
            message="该日历候选没有有效审批记录。",
            status_code=409,
        )
    return approval


async def execute_candidate(
    db: Session, item_id: UUID, decision: ApprovalDecisionRequest
) -> CalendarEventResponse:
    user_id = current_user_id(db)
    item = owned_item(db, user_id, item_id)
    if item.status not in {"pending_approval", "executing"}:
        raise AppError(
            code="CALENDAR_CANDIDATE_ALREADY_DECIDED",
            message="This calendar candidate was already decided.",
            status_code=409,
        )
    approval = pending_approval(db, user_id, item.id)
    if approval.id != decision.approval_id:
        raise AppError(code="APPROVAL_MISMATCH", message="审批记录不匹配。", status_code=409)
    now = datetime.now(UTC)
    if approval.status not in {"pending", "approved"} or approval.executed_at is not None:
        raise AppError(code="APPROVAL_ALREADY_USED", message="该审批已处理，不能重复执行。", status_code=409)
    if approval.expires_at and approval.expires_at < now:
        approval.status = "expired"
        db.commit()
        raise AppError(code="APPROVAL_EXPIRED", message="审批已过期，请重新生成候选。", status_code=409)
    actual_payload = calendar_payload(item)
    actual_hash = canonical_payload_hash(actual_payload)
    if decision.payload_hash != approval.payload_hash or actual_hash != approval.payload_hash:
        approval.status = "superseded"
        db.commit()
        raise AppError(code="APPROVAL_PAYLOAD_CHANGED", message="事件参数已变化，需要重新确认。", status_code=409)
    item.status = "executing"
    approval.status = "approved"
    approval.decided_at = approval.decided_at or now
    db.commit()

    settings = get_settings()
    result = await TOOL_REGISTRY.execute(
        db,
        name="create_calendar_event",
        user_id=user_id,
        arguments={
            "draft_id": str(item.id),
            "approval_id": str(approval.id),
            "payload_hash": actual_hash,
        },
        permissions=frozenset({"calendar:write", "calendar:read"}),
        idempotency_key=f"calendar-approval:{approval.id}",
        trace_id=None,
        timeout_seconds=settings.tool_timeout_seconds,
    )
    if not result.ok:
        raise AppError(
            code=result.error.code if result.error else "CALENDAR_TOOL_FAILED",
            message=result.error.message if result.error else "Calendar Tool failed.",
            status_code=502,
            details={"retryable": result.error.retryable if result.error else False},
        )
    db.refresh(item)
    db.refresh(approval)
    if item.status != "confirmed" or not approval.verification_result.get("verified"):
        raise AppError(
            code="CALENDAR_VERIFICATION_FAILED",
            message="事件未通过 Google Calendar 回读验证，系统不会宣称成功。",
            status_code=502,
        )
    create_episode(
        db,
        user_id,
        EpisodicMemoryCreate(
            decision="accepted",
            suggestion_type="calendar_candidate",
            summary=f"confirmed: {item.title}",
            source_email_id=item.email_id,
        ),
    )
    db.commit()
    db.refresh(item)
    return event_response(item, approval)


@router.patch("/candidates/{item_id}", response_model=CalendarEventResponse)
def update_calendar_candidate(
    item_id: UUID,
    data: CalendarEventUpdate,
    db: Session = Depends(get_db),
) -> CalendarEventResponse:
    user_id = current_user_id(db)
    item = owned_item(db, user_id, item_id)
    if item.status != "pending_approval":
        raise AppError(
            code="CALENDAR_CANDIDATE_ALREADY_DECIDED",
            message="Only pending candidates can be changed.",
            status_code=409,
        )
    old = pending_approval(db, user_id, item.id)
    updates = data.model_dump(exclude_unset=True)
    starts_at = updates.get("starts_at", item.starts_at)
    ends_at = updates.get("ends_at", item.ends_at)
    if ends_at is not None and ends_at <= starts_at:
        raise AppError(code="CALENDAR_TIME_RANGE_INVALID", message="Event end must be later than its start.", status_code=422)
    for field, value in updates.items():
        setattr(item, field, [{"email": email} for email in value] if field == "attendees" and value is not None else value)
    old.status = "superseded"
    replacement = new_calendar_approval(draft=item, user_id=user_id, agent_run_id=old.agent_run_id)
    db.add(replacement)
    db.commit()
    db.refresh(item)
    db.refresh(replacement)
    return event_response(item, replacement)


@router.post("/candidates/{item_id}/approve", response_model=CalendarEventResponse)
async def approve_candidate(
    item_id: UUID,
    decision: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
):
    return await execute_candidate(db, item_id, decision)


@router.post("/candidates/{item_id}/reject", response_model=CalendarEventResponse)
def reject_candidate(item_id: UUID, db: Session = Depends(get_db)):
    user_id = current_user_id(db)
    item = owned_item(db, user_id, item_id)
    if item.status != "pending_approval":
        raise AppError(code="CALENDAR_CANDIDATE_ALREADY_DECIDED", message="This calendar candidate was already decided.", status_code=409)
    approval = pending_approval(db, user_id, item.id)
    if approval.status != "pending":
        raise AppError(code="APPROVAL_ALREADY_USED", message="该审批已处理。", status_code=409)
    item.status = "rejected"
    approval.status = "rejected"
    approval.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(item)
    return event_response(item, approval)


@router.post("/availability", response_model=CalendarAvailabilityResponse)
async def check_calendar_availability(
    data: CalendarAvailabilityInput, db: Session = Depends(get_db)
):
    user_id = current_user_id(db)
    return await GoogleCalendarService(get_settings()).check_availability(
        db,
        google_account(db, user_id),
        start=data.starts_at,
        end=data.ends_at,
    )
