from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models.ai_output import Translation
from app.db.models.email import Email
from app.db.models.identity import EmailAccount
from app.db.session import get_db
from app.services.dify_client import DifyAPIError, DifyConfigurationError
from app.services.dify_translate_client import DifyTranslateClient
from app.services.email_processing import html_to_text, sanitize_email_html


router = APIRouter(prefix="/emails", tags=["email-translation"])


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TranslateEmailRequest(ApiModel):
    target_language: Literal["en", "zh-CN"] = "zh-CN"


class TranslateEmailResponse(ApiModel):
    email_id: UUID
    source_language: str
    target_language: str
    translated_body: str
    translated_html: str | None
    ocr_blocks: list[dict[str, object]]
    status: Literal["completed"]
    cached: bool
    workflow_run_id: str | None
    total_tokens: int | None


def get_translate_client() -> DifyTranslateClient:
    return DifyTranslateClient(get_settings())


@router.post(
    "/{email_id}/translate",
    response_model=TranslateEmailResponse,
    summary="Translate a synchronized email on demand",
)
async def translate_email(
    email_id: UUID,
    request: TranslateEmailRequest,
    db: Session = Depends(get_db),
    client: DifyTranslateClient = Depends(get_translate_client),
) -> TranslateEmailResponse:
    row = db.execute(
        select(Email, EmailAccount)
        .join(EmailAccount, Email.email_account_id == EmailAccount.id)
        .where(Email.id == email_id, EmailAccount.provider == "google")
    ).one_or_none()
    if row is None:
        raise AppError(
            code="EMAIL_NOT_FOUND",
            message="The email was not found in the connected Gmail account.",
            status_code=404,
        )
    email, _ = row

    cached = db.execute(
        select(Translation)
        .where(
            Translation.email_id == email.id,
            Translation.target_language == request.target_language,
        )
        .order_by(Translation.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if cached:
        return TranslateEmailResponse(
            email_id=email.id,
            source_language=cached.source_language or "unknown",
            target_language=cached.target_language,
            translated_body=cached.translated_body,
            translated_html=cached.translated_html,
            ocr_blocks=cached.ocr_blocks,
            status="completed",
            cached=True,
            workflow_run_id=None,
            total_tokens=0,
        )

    source_language = str(
        email.processing_metadata.get("detected_language") or "unknown"
    )
    content_type: Literal["html", "text"] = "html" if email.body_html else "text"
    content = email.body_html or email.cleaned_text or email.body_text or email.snippet or ""
    if not content.strip():
        raise AppError(
            code="EMAIL_CONTENT_EMPTY",
            message="The email has no content available for translation.",
            status_code=422,
        )

    try:
        workflow = await client.translate(
            email_id=str(email.id),
            source_language=source_language,
            target_language=request.target_language,
            content_type=content_type,
            content=content,
        )
    except DifyConfigurationError as exc:
        raise AppError(
            code="TRANSLATE_SKILL_NOT_CONFIGURED",
            message="TranslateSkill is not configured on the API server.",
            status_code=503,
        ) from exc
    except DifyAPIError as exc:
        raise AppError(
            code="TRANSLATE_SKILL_FAILED",
            message="Email translation is temporarily unavailable.",
            status_code=502,
        ) from exc

    outputs = workflow.data.outputs or {}
    translated_content = str(outputs.get("translated_content") or "").strip()
    if not translated_content or str(outputs.get("email_id")) != str(email.id):
        raise AppError(
            code="TRANSLATE_OUTPUT_INVALID",
            message="TranslateSkill returned invalid output.",
            status_code=502,
        )

    translated_html = (
        sanitize_email_html(translated_content) if content_type == "html" else None
    )
    translated_body = (
        html_to_text(translated_html or translated_content)
        if content_type == "html"
        else translated_content
    )
    record = Translation(
        email_id=email.id,
        source_language=source_language,
        target_language=request.target_language,
        translated_body=translated_body,
        translated_html=translated_html,
        ocr_blocks=[],
        model_name=("local-mock" if get_settings().dify_mock_mode else "gpt-5-mini"),
        prompt_version="translate-v1",
    )
    db.add(record)
    db.commit()

    return TranslateEmailResponse(
        email_id=email.id,
        source_language=source_language,
        target_language=request.target_language,
        translated_body=translated_body,
        translated_html=translated_html,
        ocr_blocks=[],
        status="completed",
        cached=False,
        workflow_run_id=workflow.workflow_run_id,
        total_tokens=workflow.data.total_tokens,
    )

