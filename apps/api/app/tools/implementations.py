from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.ai_output import ReplyDraft
from app.db.models.email import Email, EmailThread
from app.db.models.identity import EmailAccount
from app.db.models.productivity import CalendarDraft, Task
from app.db.models.agent import Approval
from app.schemas.rag import RagSearchRequest
from app.services.memory import get_user_preferences_tool, preference_payload, get_or_create_preferences
from app.services.rag import EmbeddingClient, RagService
from app.tools.base import BaseTool, ToolContext, ToolExecutionError
from app.services.approval import calendar_payload, canonical_payload_hash, new_calendar_approval
from app.services.google_calendar import GoogleCalendarService, verify_event


class EmailIdInput(BaseModel):
    email_id: UUID


class ThreadIdInput(BaseModel):
    thread_id: UUID


class SearchEmailsInput(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=20)


class RelatedEmailsInput(BaseModel):
    email_id: UUID
    query: str = Field(min_length=2, max_length=1000)
    top_k: int = Field(default=4, ge=3, le=5)


class EmptyInput(BaseModel):
    pass


class CreateTaskInput(BaseModel):
    email_id: UUID | None = None
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    priority: Literal["low", "normal", "high"] = "normal"
    due_at: datetime | None = None


class CreateReplyDraftInput(BaseModel):
    email_id: UUID
    subject: str = Field(min_length=1, max_length=1000)
    body: str = Field(min_length=1, max_length=20000)
    tone: Literal["professional", "friendly", "concise", "formal"] | None = None
    language: str | None = Field(default=None, max_length=16)


class CalendarWindowInput(BaseModel):
    starts_at: datetime
    ends_at: datetime


class CreateCalendarDraftInput(BaseModel):
    email_id: UUID | None = None
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = Field(min_length=1, max_length=64)
    location: str | None = Field(default=None, max_length=500)
    attendees: list[str] = Field(default_factory=list, max_length=50)
    evidence: str = Field(min_length=1, max_length=2000)


class CalendarApprovalInput(BaseModel):
    draft_id: UUID
    approval_id: UUID
    payload_hash: str = Field(min_length=64, max_length=64)


class GetCalendarEventInput(BaseModel):
    draft_id: UUID


def _owned_email(db: Session, user_id: UUID, email_id: UUID) -> Email:
    email = db.scalar(
        select(Email)
        .join(EmailAccount, Email.email_account_id == EmailAccount.id)
        .where(Email.id == email_id, EmailAccount.user_id == user_id)
    )
    if email is None:
        # Deliberately use the same response for missing and foreign resources.
        raise ToolExecutionError("RESOURCE_NOT_FOUND", "Email was not found.")
    return email


def _email_data(email: Email, *, include_body: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": str(email.id),
        "thread_id": str(email.thread_id) if email.thread_id else None,
        "subject": email.subject or "(no subject)",
        "sender": email.sender,
        "recipients": email.recipients,
        "sent_at": (email.sent_at or email.received_at).isoformat(),
        "labels": email.labels,
    }
    if include_body:
        result["body"] = email.cleaned_text or email.body_text or email.snippet or ""
    else:
        result["preview"] = email.snippet or ""
    return result


def _google_account(db: Session, user_id: UUID) -> EmailAccount:
    account = db.scalar(
        select(EmailAccount).where(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == "google",
            EmailAccount.sync_status == "connected",
        )
    )
    if account is None:
        raise ToolExecutionError("GOOGLE_CALENDAR_NOT_CONNECTED", "Google account is not connected.")
    return account


def _owned_calendar_draft(db: Session, user_id: UUID, draft_id: UUID) -> CalendarDraft:
    draft = db.scalar(select(CalendarDraft).where(CalendarDraft.id == draft_id, CalendarDraft.user_id == user_id))
    if draft is None:
        raise ToolExecutionError("RESOURCE_NOT_FOUND", "Calendar draft was not found.")
    return draft


class GetEmailTool(BaseTool[EmailIdInput]):
    name, permission, input_model = "get_email", "email:read", EmailIdInput
    description = "Read one email owned by the requesting user."

    async def execute(self, db: Session, context: ToolContext, arguments: EmailIdInput):
        return _email_data(_owned_email(db, context.user_id, arguments.email_id))


class GetEmailThreadTool(BaseTool[ThreadIdInput]):
    name, permission, input_model = "get_email_thread", "email:read", ThreadIdInput
    description = "Read an owned email thread in chronological order."

    async def execute(self, db: Session, context: ToolContext, arguments: ThreadIdInput):
        thread = db.scalar(
            select(EmailThread)
            .join(EmailAccount, EmailThread.email_account_id == EmailAccount.id)
            .where(EmailThread.id == arguments.thread_id, EmailAccount.user_id == context.user_id)
        )
        if thread is None:
            raise ToolExecutionError("RESOURCE_NOT_FOUND", "Email thread was not found.")
        emails = db.scalars(select(Email).where(Email.thread_id == thread.id).order_by(Email.received_at)).all()
        return {"thread_id": str(thread.id), "subject": thread.subject, "messages": [_email_data(item) for item in emails]}


class SearchEmailsTool(BaseTool[SearchEmailsInput]):
    name, permission, input_model = "search_emails", "email:read", SearchEmailsInput
    description = "Search the requesting user's mailbox by subject, sender, or clean text."

    async def execute(self, db: Session, context: ToolContext, arguments: SearchEmailsInput):
        pattern = f"%{arguments.query}%"
        rows = db.scalars(
            select(Email)
            .join(EmailAccount, Email.email_account_id == EmailAccount.id)
            .where(
                EmailAccount.user_id == context.user_id,
                or_(Email.subject.ilike(pattern), Email.snippet.ilike(pattern), Email.cleaned_text.ilike(pattern), Email.sender["email"].as_string().ilike(pattern)),
            )
            .order_by(Email.received_at.desc())
            .limit(arguments.limit)
        ).all()
        return {"query": arguments.query, "count": len(rows), "emails": [_email_data(item, include_body=False) for item in rows]}


class RetrieveRelatedEmailsTool(BaseTool[RelatedEmailsInput]):
    name, permission, input_model = "retrieve_related_emails", "email:read", RelatedEmailsInput
    description = "Retrieve semantically related owned email evidence with citations."

    async def execute(self, db: Session, context: ToolContext, arguments: RelatedEmailsInput):
        _owned_email(db, context.user_id, arguments.email_id)
        settings = get_settings()
        result = await RagService(settings, EmbeddingClient(settings)).search(
            db,
            RagSearchRequest(user_id=context.user_id, email_id=arguments.email_id, query=arguments.query, top_k=arguments.top_k),
        )
        return result.model_dump(mode="json")


class GetUserPreferencesTool(BaseTool[EmptyInput]):
    name, permission, input_model = "get_user_preferences", "preferences:read", EmptyInput
    description = "Read explicit preferences and active episodic guidance, never email facts."

    async def execute(self, db: Session, context: ToolContext, arguments: EmptyInput):
        return get_user_preferences_tool(db, context.user_id).model_dump(mode="json")


class CreateTaskTool(BaseTool[CreateTaskInput]):
    name, permission, input_model = "create_task", "task:write", CreateTaskInput
    description = "Create a task for the requesting user."

    async def execute(self, db: Session, context: ToolContext, arguments: CreateTaskInput):
        if arguments.email_id:
            _owned_email(db, context.user_id, arguments.email_id)
        task = Task(user_id=context.user_id, email_id=arguments.email_id, title=arguments.title, description=arguments.description, priority=arguments.priority, due_at=arguments.due_at, source_evidence={"source": "tool", "trace_id": context.trace_id})
        db.add(task)
        db.flush()
        return {"id": str(task.id), "status": task.status, "title": task.title, "due_at": task.due_at.isoformat() if task.due_at else None}


class CreateReplyDraftTool(BaseTool[CreateReplyDraftInput]):
    name, permission, input_model = "create_reply_draft", "draft:write", CreateReplyDraftInput
    description = "Create a reviewable reply draft without sending email."

    async def execute(self, db: Session, context: ToolContext, arguments: CreateReplyDraftInput):
        email = _owned_email(db, context.user_id, arguments.email_id)
        preferences = preference_payload(get_or_create_preferences(db, context.user_id))
        draft = ReplyDraft(email_id=email.id, user_id=context.user_id, status="draft", tone=arguments.tone or preferences.reply_tone, language=arguments.language or preferences.default_language, subject=arguments.subject, body=arguments.body, generation_context={"source": "tool", "trace_id": context.trace_id, "requires_approval": True})
        db.add(draft)
        db.flush()
        return {"id": str(draft.id), "status": draft.status, "subject": draft.subject, "tone": draft.tone, "language": draft.language, "requires_approval": True}


class CheckCalendarAvailabilityTool(BaseTool[CalendarWindowInput]):
    name, permission, input_model = "check_calendar_availability", "calendar:read", CalendarWindowInput
    description = "Check the user's real Google Calendar before proposing a meeting."

    async def execute(self, db: Session, context: ToolContext, arguments: CalendarWindowInput):
        if arguments.starts_at.tzinfo is None or arguments.ends_at.tzinfo is None or arguments.ends_at <= arguments.starts_at:
            raise ToolExecutionError("CALENDAR_TIME_INVALID", "Calendar range must be explicit, timezone-aware, and ordered.")
        return await GoogleCalendarService(get_settings()).check_availability(db, _google_account(db, context.user_id), start=arguments.starts_at, end=arguments.ends_at)


class CreateCalendarDraftTool(BaseTool[CreateCalendarDraftInput]):
    name, permission, input_model = "create_calendar_draft", "calendar:write", CreateCalendarDraftInput
    description = "Create an evidence-backed calendar draft and approval; never creates a Google event."

    async def execute(self, db: Session, context: ToolContext, arguments: CreateCalendarDraftInput):
        if arguments.starts_at.tzinfo is None or (arguments.ends_at and arguments.ends_at.tzinfo is None):
            raise ToolExecutionError("CALENDAR_DATE_AMBIGUOUS", "Date and time must include a timezone before approval.")
        if arguments.ends_at and arguments.ends_at <= arguments.starts_at:
            raise ToolExecutionError("CALENDAR_TIME_INVALID", "Event end must be after its start.")
        if arguments.email_id:
            _owned_email(db, context.user_id, arguments.email_id)
        draft = CalendarDraft(user_id=context.user_id, email_id=arguments.email_id, status="pending_approval", title=arguments.title, description=arguments.description, starts_at=arguments.starts_at, ends_at=arguments.ends_at, timezone=arguments.timezone, location=arguments.location, attendees=[{"email": value} for value in arguments.attendees], source_evidence={"text": arguments.evidence, "source": "tool", "untrusted_input": True})
        db.add(draft)
        db.flush()
        approval = new_calendar_approval(draft=draft, user_id=context.user_id)
        db.add(approval)
        db.flush()
        return {"draft_id": str(draft.id), "approval_id": str(approval.id), "payload_hash": approval.payload_hash, "expires_at": approval.expires_at.isoformat(), "status": draft.status, "requires_approval": True}


class CreateCalendarEventTool(BaseTool[CalendarApprovalInput]):
    name, permission, input_model = "create_calendar_event", "calendar:write", CalendarApprovalInput
    description = "Create and verify a Google Calendar event only from a valid user approval."

    async def execute(self, db: Session, context: ToolContext, arguments: CalendarApprovalInput):
        draft = _owned_calendar_draft(db, context.user_id, arguments.draft_id)
        approval = db.scalar(select(Approval).where(Approval.id == arguments.approval_id, Approval.user_id == context.user_id, Approval.resource_id == draft.id))
        payload = calendar_payload(draft)
        payload_hash = canonical_payload_hash(payload)
        now = datetime.now(UTC)
        if approval is None or approval.status != "approved":
            raise ToolExecutionError("APPROVAL_REQUIRED", "An explicit, valid user approval is required.")
        if approval.executed_at or draft.provider_event_id:
            raise ToolExecutionError("APPROVAL_ALREADY_USED", "This approval has already been executed.")
        if approval.expires_at and approval.expires_at < now:
            raise ToolExecutionError("APPROVAL_EXPIRED", "The approval has expired.")
        if arguments.payload_hash != approval.payload_hash or payload_hash != approval.payload_hash:
            raise ToolExecutionError("APPROVAL_PAYLOAD_CHANGED", "Calendar parameters changed after approval.")
        service = GoogleCalendarService(get_settings())
        account = _google_account(db, context.user_id)
        event_id = f"mailpilot{draft.id.hex}"
        created = await service.create_event(db, account, event_id=event_id, payload=payload)
        actual = await service.get_event(db, account, event_id=created["id"])
        verification = verify_event(payload, actual)
        draft.provider_event_id = created["id"]
        approval.executed_at = now
        approval.verification_result = verification
        if not verification["verified"]:
            draft.status, approval.status = "verification_failed", "verification_failed"
            return {"draft_id": str(draft.id), "event_id": created["id"], "verified": False, "verification": verification}
        draft.status, approval.status = "confirmed", "executed"
        return {"draft_id": str(draft.id), "event_id": created["id"], "verified": True, "verification": verification}


class GetCalendarEventTool(BaseTool[GetCalendarEventInput]):
    name, permission, input_model = "get_calendar_event", "calendar:read", GetCalendarEventInput
    description = "Read a previously created Google Calendar event and its verification state."

    async def execute(self, db: Session, context: ToolContext, arguments: GetCalendarEventInput):
        draft = _owned_calendar_draft(db, context.user_id, arguments.draft_id)
        if not draft.provider_event_id:
            raise ToolExecutionError("CALENDAR_EVENT_NOT_CREATED", "The draft has no provider event ID.")
        actual = await GoogleCalendarService(get_settings()).get_event(db, _google_account(db, context.user_id), event_id=draft.provider_event_id)
        verification = verify_event(calendar_payload(draft), actual)
        return {"draft_id": str(draft.id), "event_id": draft.provider_event_id, "event": actual, "verification": verification}


TOOLS = [GetEmailTool(), GetEmailThreadTool(), SearchEmailsTool(), RetrieveRelatedEmailsTool(), GetUserPreferencesTool(), CreateTaskTool(), CreateReplyDraftTool(), CheckCalendarAvailabilityTool(), CreateCalendarDraftTool(), CreateCalendarEventTool(), GetCalendarEventTool()]
