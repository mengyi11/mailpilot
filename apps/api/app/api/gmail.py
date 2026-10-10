from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models.email import Email
from app.db.models.ai_output import Translation as TranslationModel
from app.db.models.identity import EmailAccount
from app.db.session import get_db
from app.services.gmail_sync import GmailSyncResult, GmailSyncService


router = APIRouter(prefix="/gmail", tags=["gmail"])


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EmailAddress(ApiModel):
    name: str
    email: str


class AiOverview(ApiModel):
    summary: str
    category: str
    priority: str
    confidence: float


class Translation(ApiModel):
    source_language: str
    target_language: str
    translated_body: str
    translated_html: str | None
    ocr_blocks: list[dict]
    status: str


class ReplyDraft(ApiModel):
    subject: str
    body: str
    tone: str
    language: str


class GmailEmail(ApiModel):
    id: str
    subject: str
    sender: EmailAddress
    preview: str
    received_at: datetime
    is_read: bool
    is_starred: bool
    labels: list[str]
    priority: str
    recipients: list[EmailAddress]
    body_text: str
    body_html: str | None
    ai_overview: AiOverview
    translation: Translation
    action_items: list[dict]
    calendar_drafts: list[dict]
    reply_draft: ReplyDraft


class SyncResponse(ApiModel):
    account_id: str
    requested: int
    fetched: int
    created: int
    updated: int
    skipped: int
    failed: int
    mode: str
    history_id: str | None


def _connected_account(db: Session) -> EmailAccount:
    account = db.scalar(
        select(EmailAccount)
        .options(selectinload(EmailAccount.oauth_credential))
        .where(
            EmailAccount.provider == "google",
            EmailAccount.sync_status.in_(["connected", "syncing", "error"]),
        )
        .order_by(EmailAccount.updated_at.desc())
    )
    if account is None or account.oauth_credential is None:
        raise AppError(
            code="GMAIL_ACCOUNT_NOT_CONNECTED",
            message="Connect a Gmail account before syncing mail.",
            status_code=409,
        )
    return account


@router.post("/sync", response_model=SyncResponse, summary="Sync up to 15 Gmail messages")
async def sync_gmail(
    limit: int = Query(default=15, ge=1, le=15),
    db: Session = Depends(get_db),
) -> GmailSyncResult:
    account = _connected_account(db)
    return await GmailSyncService(get_settings()).sync(db, account, limit=limit)


@router.get("/emails", response_model=list[GmailEmail], summary="List synchronized Gmail messages")
async def list_gmail_emails(
    limit: int = Query(default=15, ge=1, le=15),
    db: Session = Depends(get_db),
) -> list[GmailEmail]:
    account = _connected_account(db)
    emails = db.scalars(
        select(Email)
        .where(Email.email_account_id == account.id)
        .order_by(Email.received_at.desc())
        .limit(limit)
    ).all()
    email_ids = [email.id for email in emails]
    translations = {
        item.email_id: item
        for item in db.scalars(
            select(TranslationModel)
            .where(TranslationModel.email_id.in_(email_ids))
            .order_by(TranslationModel.email_id, TranslationModel.created_at.desc())
            .distinct(TranslationModel.email_id)
        ).all()
    }
    response: list[GmailEmail] = []
    for email in emails:
        saved_translation = translations.get(email.id)
        recipients = email.recipients.get("to", []) + email.recipients.get("cc", [])
        response.append(
            GmailEmail(
                id=str(email.id),
                subject=email.subject or "(no subject)",
                sender=EmailAddress(**email.sender),
                preview=email.snippet or "",
                received_at=email.received_at,
                is_read=email.is_read,
                is_starred=email.is_starred,
                labels=email.labels,
                priority="high" if "IMPORTANT" in email.labels else "normal",
                recipients=[EmailAddress(**item) for item in recipients],
                body_text=email.body_text or email.snippet or "",
                body_html=email.body_html,
                ai_overview=AiOverview(
                    summary="尚未运行AI分析。邮件已从Gmail安全同步。",
                    category="待分析",
                    priority="high" if "IMPORTANT" in email.labels else "normal",
                    confidence=0,
                ),
                translation=Translation(
                    source_language=(
                        saved_translation.source_language
                        if saved_translation
                        else "unknown"
                    ),
                    target_language=(
                        saved_translation.target_language
                        if saved_translation
                        else "简体中文"
                    ),
                    translated_body=(
                        saved_translation.translated_body if saved_translation else ""
                    ),
                    translated_html=(
                        saved_translation.translated_html if saved_translation else None
                    ),
                    ocr_blocks=(
                        saved_translation.ocr_blocks if saved_translation else []
                    ),
                    status="completed" if saved_translation else "pending",
                ),
                action_items=[],
                calendar_drafts=[],
                reply_draft=ReplyDraft(
                    subject=f"Re: {email.subject or ''}",
                    body="",
                    tone="未生成",
                    language="unknown",
                ),
            )
        )
    return response
