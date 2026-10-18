from __future__ import annotations

import json
import re
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
from app.schemas.structured_output import (
    EmailAnalysis as StructuredEmailAnalysis,
    EmailPriority,
    ExtractedDate,
)
from app.services.dify_client import (
    DifyAPIError,
    DifyClient,
    DifyConfigurationError,
    DifyEmailInput,
)
from app.services.schema_repair import (
    StrongModelRepairClient,
    decode_json_payload,
    repair_analysis_payload,
    safe_read_only_analysis,
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
    priority: EmailPriority
    summary: str
    summary_en: str | None
    summary_zh: str | None
    translation_needed: bool
    actions: list[ActionItem]
    calendar_candidates: list[CalendarDraftResponse]
    workflow_run_id: str
    elapsed_time: float | None
    total_tokens: int | None
    validation_mode: str
    read_only: bool


def get_dify_client() -> DifyClient:
    return DifyClient(get_settings())


def get_repair_client() -> StrongModelRepairClient:
    return StrongModelRepairClient(get_settings())


def _analysis_payload(outputs: dict[str, Any] | None) -> dict[str, Any]:
    if not outputs or "analysis" not in outputs:
        raise AppError(
            code="DIFY_OUTPUT_INVALID",
            message="Dify did not return the required analysis output.",
            status_code=502,
        )

    try:
        return decode_json_payload(outputs["analysis"])
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AppError(
            code="DIFY_OUTPUT_INVALID",
            message="Dify returned analysis data that failed validation.",
            status_code=502,
            details={"validation": str(exc)},
        ) from exc


def _parse_dify_analysis(outputs: dict[str, Any] | None) -> StructuredEmailAnalysis:
    payload = _analysis_payload(outputs)
    try:
        return StructuredEmailAnalysis.model_validate(payload)
    except ValidationError as exc:
        raise AppError(
            code="DIFY_OUTPUT_INVALID",
            message="Dify returned analysis data that failed validation.",
            status_code=502,
            details={"validation": str(exc)},
        ) from exc


async def _validate_or_repair_analysis(
    outputs: dict[str, Any] | None,
    *,
    expected_email_id: UUID,
    repair_client: StrongModelRepairClient,
) -> tuple[StructuredEmailAnalysis, str, bool]:
    try:
        result = _parse_dify_analysis(outputs)
        if result.email_id != expected_email_id:
            raise AppError(
                code="DIFY_EMAIL_ID_MISMATCH",
                message="Dify returned a result for a different email.",
                status_code=502,
            )
        return result, "strict", False
    except AppError:
        try:
            payload = _analysis_payload(outputs)
            repaired = repair_analysis_payload(
                payload,
                expected_email_id=expected_email_id,
            )
            return repaired, "schema_repair", False
        except (AppError, TypeError, ValueError, ValidationError):
            payload = None
            try:
                payload = _analysis_payload(outputs)
            except AppError:
                pass
            if payload is not None:
                try:
                    strong_payload = await repair_client.repair(
                        email_id=expected_email_id,
                        raw_analysis=payload,
                    )
                    repaired = StructuredEmailAnalysis.model_validate(strong_payload)
                    if repaired.email_id != expected_email_id:
                        raise ValueError("Strong model returned a different email_id")
                    return repaired, "strong_model_repair", False
                except (
                    DifyAPIError,
                    DifyConfigurationError,
                    TypeError,
                    ValueError,
                    ValidationError,
                ):
                    pass
            return (
                safe_read_only_analysis(email_id=expected_email_id, payload=payload),
                "read_only_fallback",
                True,
            )


def _sender_text(sender: dict[str, Any]) -> str:
    name = str(sender.get("name") or "").strip()
    address = str(sender.get("email") or "").strip()
    if name and address:
        return f"{name} <{address}>"
    return address or name or "unknown"


def _split_bilingual_summary(summary: str) -> tuple[str, str | None, str | None]:
    """Split the compact ZH/EN contract while remaining compatible with old runs."""
    normalized = summary.strip()
    match = re.fullmatch(
        r"\s*ZH\s*[:：]\s*(.*?)\s*\n+\s*EN\s*[:：]\s*(.*?)\s*",
        normalized,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        zh, en = (value.strip() for value in match.groups())
        return en, en, zh
    match = re.fullmatch(
        r"\s*EN\s*[:：]\s*(.*?)\s*\n+\s*ZH\s*[:：]\s*(.*?)\s*",
        normalized,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        en, zh = (value.strip() for value in match.groups())
        return en, en, zh
    if any("\u4e00" <= character <= "\u9fff" for character in normalized):
        return normalized, None, normalized
    return normalized, normalized, None


@router.post(
    "/{email_id}/analyze",
    response_model=AnalyzeEmailResponse,
    summary="Analyze a synchronized email with the Dify workflow",
)
async def analyze_email(
    email_id: UUID,
    db: Session = Depends(get_db),
    dify: DifyClient = Depends(get_dify_client),
    repair_client: StrongModelRepairClient = Depends(get_repair_client),
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
        result, validation_mode, read_only = await _validate_or_repair_analysis(
            workflow.data.outputs,
            expected_email_id=email.id,
            repair_client=repair_client,
        )
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

    display_summary, summary_en, summary_zh = _split_bilingual_summary(result.summary)
    completed_at = datetime.now(UTC)
    structured_output = result.model_dump(mode="json", by_alias=False)
    structured_output["summary_en"] = summary_en
    structured_output["summary_zh"] = summary_zh
    structured_output["validation_mode"] = validation_mode
    structured_output["read_only"] = read_only
    evidence = [
        {
            "type": "calendar_candidate",
            "text": item.evidence.text,
            "confidence": item.confidence,
        }
        for item in result.extracted_dates
    ]
    confidences = [item.confidence for item in result.extracted_dates]
    analysis = EmailAnalysis(
        email_id=email.id,
        status="read_only" if read_only else "completed",
        model_provider=("mock" if get_settings().dify_mock_mode else "openai"),
        model_name=(
            "local-mock" if get_settings().dify_mock_mode else get_settings().dify_fast_model
        ),
        prompt_version=(
            "local-mock-v1"
            if get_settings().dify_mock_mode
            else "dify-email-analysis-v1"
        ),
        detected_language=language,
        summary=display_summary,
        category=result.category,
        priority=result.priority,
        action_items=[item.model_dump(mode="json") for item in result.actions],
        extracted_dates=[
            item.model_dump(mode="json") for item in result.extracted_dates
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

    drafts: list[tuple[CalendarDraft, ExtractedDate]] = []
    for candidate in ([] if read_only else result.extracted_dates):
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
                "text": candidate.evidence.text,
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
        priority=result.priority,
        summary=display_summary,
        summary_en=summary_en,
        summary_zh=summary_zh,
        translation_needed=result.translation_needed,
        actions=[
            ActionItem(
                title=item.title,
                description=item.description,
                due_at=item.due_at,
                evidence=item.evidence.text,
                confidence=item.confidence,
            )
            for item in result.actions
        ],
        calendar_candidates=[
            CalendarDraftResponse(
                id=draft.id,
                title=draft.title,
                starts_at=draft.starts_at,
                ends_at=draft.ends_at,
                timezone=draft.timezone,
                location=draft.location,
                evidence=candidate.evidence.text,
                confidence=candidate.confidence,
                status=draft.status,
            )
            for draft, candidate in drafts
        ],
        workflow_run_id=workflow.workflow_run_id,
        elapsed_time=workflow.data.elapsed_time,
        total_tokens=workflow.data.total_tokens,
        validation_mode=validation_mode,
        read_only=read_only,
    )
