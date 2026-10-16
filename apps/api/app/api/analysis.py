from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models.ai_output import EmailAnalysis
from app.db.models.email import Email
from app.db.models.identity import EmailAccount
from app.db.models.productivity import CalendarDraft
from app.db.session import get_db
from app.services.dify_client import (
    DifyAPIError,
    DifyClient,
    DifyConfigurationError,
    DifyEmailInput,
)


router = APIRouter(prefix="/emails", tags=["email-analysis"])


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ActionItem(ApiModel):
    title: str = Field(min_length=1)
    description: str | None = None
    due_at: datetime | None = None
    evidence: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class CalendarCandidate(ApiModel):
    title: str = Field(min_length=1)
    start: datetime
    end: datetime | None = None
    timezone: str = Field(min_length=1)
    location: str | None = None
    description: str | None = None
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class DifyAnalysisResult(ApiModel):
    email_id: UUID
    category: str = Field(min_length=1, max_length=64)
    summary: str = Field(min_length=1)
    translation_needed: bool
    actions: list[ActionItem] = Field(default_factory=list)
    calendar_candidates: list[CalendarCandidate] = Field(default_factory=list)


class CalendarDraftResponse(ApiModel):
    id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    location: str | None
    evidence: str
    confidence: float
    status: str


class AnalyzeEmailResponse(ApiModel):
    analysis_id: UUID
    email_id: UUID
    status: str
    category: str
    summary: str
    translation_needed: bool
    actions: list[ActionItem]
    calendar_candidates: list[CalendarDraftResponse]
    workflow_run_id: str
    elapsed_time: float | None
    total_tokens: int | None


def get_dify_client() -> DifyClient:
    return DifyClient(get_settings())


def _parse_dify_analysis(outputs: dict[str, Any] | None) -> DifyAnalysisResult:
    if not outputs or "analysis" not in outputs:
        raise AppError(
            code="DIFY_OUTPUT_INVALID",
            message="Dify did not return the required analysis output.",
            status_code=502,
        )

    raw = outputs["analysis"]
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
        return DifyAnalysisResult.model_validate(payload)
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        raise AppError(
            code="DIFY_OUTPUT_INVALID",
            message="Dify returned analysis data that failed validation.",
            status_code=502,
            details={"validation": str(exc)},
        ) from exc


def _sender_text(sender: dict[str, Any]) -> str:
    name = str(sender.get("name") or "").strip()
    address = str(sender.get("email") or "").strip()
    if name and address:
        return f"{name} <{address}>"
    return address or name or "unknown"


@router.post(
    "/{email_id}/analyze",
    response_model=AnalyzeEmailResponse,
    summary="Analyze a synchronized email with the Dify workflow",
)
async def analyze_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    dify: DifyClient = Depends(get_dify_client),
) -> AnalyzeEmailResponse:
    row = db.execute(
        select(Email, EmailAccount)
        .join(EmailAccount, Email.email_account_id == EmailAccount.id)
        .where(
            Email.id == email_id,
            EmailAccount.provider == "google",
            EmailAccount.sync_status.in_(["connected", "syncing", "error"]),
        )
    ).one_or_none()
    if row is None:
        raise AppError(
            code="EMAIL_NOT_FOUND",
            message="The email was not found in the connected Gmail account.",
            status_code=404,
        )

    email, account = row
    cleaned_body = (email.cleaned_text or email.body_text or email.snippet or "").strip()
    if not cleaned_body:
        raise AppError(
            code="EMAIL_CONTENT_EMPTY",
            message="The email has no cleaned text available for analysis.",
            status_code=422,
        )

    language = str(email.processing_metadata.get("detected_language") or "unknown")
    sent_at = email.sent_at or email.received_at
    started_at = datetime.now(UTC)

    try:
        workflow = await dify.run_email_workflow(
            DifyEmailInput(
                user_id=str(account.user_id),
                email_id=str(email.id),
                subject=email.subject or "(no subject)",
                sender=_sender_text(email.sender),
                sent_at=sent_at,
                body=cleaned_body,
                language=language,
                timezone=email.user_timezone,
            )
        )
        result = _parse_dify_analysis(workflow.data.outputs)
    except DifyConfigurationError as exc:
        raise AppError(
            code="DIFY_NOT_CONFIGURED",
            message="Dify is not configured on the API server.",
            status_code=503,
        ) from exc
    except DifyAPIError as exc:
        raise AppError(
            code="DIFY_REQUEST_FAILED",
            message="The email analysis service is temporarily unavailable.",
            status_code=502,
        ) from exc

    if result.email_id != email.id:
        raise AppError(
            code="DIFY_EMAIL_ID_MISMATCH",
            message="Dify returned a result for a different email.",
            status_code=502,
        )

    completed_at = datetime.now(UTC)
    structured_output = result.model_dump(mode="json", by_alias=False)
    evidence = [
        {
            "type": "calendar_candidate",
            "text": item.evidence,
            "confidence": item.confidence,
        }
        for item in result.calendar_candidates
    ]
    confidences = [item.confidence for item in result.calendar_candidates]
    analysis = EmailAnalysis(
        email_id=email.id,
        status="completed",
        model_provider="openai",
        model_name=get_settings().dify_fast_model,
        prompt_version="dify-email-analysis-v1",
        detected_language=language,
        summary=result.summary,
        category=result.category,
        action_items=[item.model_dump(mode="json") for item in result.actions],
        extracted_dates=[
            item.model_dump(mode="json") for item in result.calendar_candidates
        ],
        evidence=evidence,
        confidence=(
            Decimal(str(sum(confidences) / len(confidences)))
            if confidences
            else None
        ),
        structured_output=structured_output,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(analysis)
    db.flush()

    drafts: list[tuple[CalendarDraft, CalendarCandidate]] = []
    for candidate in result.calendar_candidates:
        draft = CalendarDraft(
            user_id=account.user_id,
            email_id=email.id,
            analysis_id=analysis.id,
            status="pending_approval",
            title=candidate.title,
            description=candidate.description,
            starts_at=candidate.start,
            ends_at=candidate.end,
            timezone=candidate.timezone,
            location=candidate.location,
            source_evidence={
                "text": candidate.evidence,
                "confidence": candidate.confidence,
                "workflow_run_id": workflow.workflow_run_id,
            },
        )
        db.add(draft)
        drafts.append((draft, candidate))

    db.commit()

    return AnalyzeEmailResponse(
        analysis_id=analysis.id,
        email_id=email.id,
        status=analysis.status,
        category=result.category,
        summary=result.summary,
        translation_needed=result.translation_needed,
        actions=result.actions,
        calendar_candidates=[
            CalendarDraftResponse(
                id=draft.id,
                title=draft.title,
                starts_at=draft.starts_at,
                ends_at=draft.ends_at,
                timezone=draft.timezone,
                location=draft.location,
                evidence=candidate.evidence,
                confidence=candidate.confidence,
                status=draft.status,
            )
            for draft, candidate in drafts
        ],
        workflow_run_id=workflow.workflow_run_id,
        elapsed_time=workflow.data.elapsed_time,
        total_tokens=workflow.data.total_tokens,
    )
