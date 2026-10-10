import asyncio
import base64
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from email.header import decode_header, make_header
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models.email import Attachment, Email, EmailThread
from app.db.models.identity import EmailAccount
from app.db.models.productivity import UserPreference
from app.services.email_processing import (
    ALLOWED_ATTACHMENT_TYPES,
    extract_attachment_text,
    process_email_content,
)
from app.services.google_oauth import GoogleOAuthService


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() in {"style", "script", "head", "title"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"style", "script", "head", "title"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        value = data.strip()
        if value:
            self.parts.append(value)

    def text(self) -> str:
        return "\n".join(self.parts)


@dataclass(frozen=True)
class ParsedAttachment:
    provider_attachment_id: str
    filename: str
    mime_type: str | None
    size_bytes: int | None
    content_id: str | None
    is_inline: bool
    extraction_status: str = "metadata_only"
    extracted_text: str | None = None
    extraction_error: str | None = None


@dataclass(frozen=True)
class ParsedGmailMessage:
    provider_message_id: str
    provider_thread_id: str
    internet_message_id: str | None
    sender: dict[str, str]
    recipients: dict[str, list[dict[str, str]]]
    subject: str
    snippet: str
    body_text: str
    body_html: str | None
    raw_body_html: str | None
    cleaned_text: str
    original_timezone: str
    user_timezone: str
    reference_date: str
    processing_metadata: dict[str, Any]
    received_at: datetime
    sent_at: datetime | None
    labels: list[str]
    is_read: bool
    is_starred: bool
    raw_metadata: dict[str, Any]
    attachments: list[ParsedAttachment] = field(default_factory=list)


@dataclass(frozen=True)
class GmailSyncResult:
    account_id: str
    requested: int
    fetched: int
    created: int
    updated: int
    skipped: int
    failed: int
    mode: str
    history_id: str | None


def _decode_base64url(value: str | None) -> str:
    if not value:
        return ""
    padding = "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(value + padding)
    return raw.decode("utf-8", errors="replace")


def _decode_base64url_bytes(value: str | None) -> bytes:
    if not value:
        return b""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (LookupError, UnicodeDecodeError):
        return value


def _addresses(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    return [
        {"name": _decode_header(name), "email": address.lower()}
        for name, address in getaddresses([value])
        if address
    ]


def _header_map(payload: dict[str, Any]) -> dict[str, str]:
    return {
        item["name"].lower(): item.get("value", "")
        for item in payload.get("headers", [])
        if item.get("name")
    }


def _walk_parts(
    part: dict[str, Any],
    *,
    texts: list[str],
    htmls: list[str],
    attachments: list[ParsedAttachment],
) -> None:
    mime_type = part.get("mimeType", "")
    body = part.get("body", {})
    filename = _decode_header(part.get("filename"))
    headers = _header_map(part)
    attachment_id = body.get("attachmentId")

    if attachment_id:
        attachments.append(
            ParsedAttachment(
                provider_attachment_id=attachment_id,
                filename=filename or "unnamed-attachment",
                mime_type=mime_type or None,
                size_bytes=body.get("size"),
                content_id=headers.get("content-id"),
                is_inline="inline" in headers.get("content-disposition", "").lower(),
            )
        )
    elif mime_type == "text/plain":
        content = _decode_base64url(body.get("data"))
        if content:
            texts.append(content)
    elif mime_type == "text/html":
        content = _decode_base64url(body.get("data"))
        if content:
            htmls.append(content)

    for child in part.get("parts", []):
        _walk_parts(child, texts=texts, htmls=htmls, attachments=attachments)


def parse_gmail_message(
    payload: dict[str, Any], *, user_timezone: str = "Asia/Singapore"
) -> ParsedGmailMessage:
    message_payload = payload.get("payload", {})
    headers = _header_map(message_payload)
    texts: list[str] = []
    htmls: list[str] = []
    attachments: list[ParsedAttachment] = []
    _walk_parts(
        message_payload, texts=texts, htmls=htmls, attachments=attachments
    )

    body_html = "\n".join(htmls) or None
    body_text = "\n".join(texts).strip()
    if not body_text and body_html:
        extractor = _HTMLTextExtractor()
        extractor.feed(body_html)
        body_text = extractor.text()

    sender_values = _addresses(headers.get("from"))
    sender = sender_values[0] if sender_values else {
        "name": "Unknown sender",
        "email": "unknown@invalid.local",
    }
    recipients = {
        "to": _addresses(headers.get("to")),
        "cc": _addresses(headers.get("cc")),
        "bcc": _addresses(headers.get("bcc")),
    }
    internal_date = datetime.fromtimestamp(
        int(payload["internalDate"]) / 1000, tz=UTC
    )
    sent_at: datetime | None = None
    if headers.get("date"):
        try:
            sent_at = parsedate_to_datetime(headers["date"])
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=UTC)
        except (TypeError, ValueError, OverflowError):
            sent_at = None

    effective_sent_at = sent_at or internal_date
    processed = process_email_content(
        body_html=body_html,
        body_text=body_text or payload.get("snippet", ""),
        sent_at=effective_sent_at,
        user_timezone=user_timezone,
    )

    labels = payload.get("labelIds", [])
    return ParsedGmailMessage(
        provider_message_id=payload["id"],
        provider_thread_id=payload["threadId"],
        internet_message_id=headers.get("message-id"),
        sender=sender,
        recipients=recipients,
        subject=_decode_header(headers.get("subject")) or "(no subject)",
        snippet=payload.get("snippet", ""),
        body_text=processed.plain_text,
        body_html=processed.safe_html,
        raw_body_html=body_html,
        cleaned_text=processed.cleaned_text,
        original_timezone=processed.original_timezone,
        user_timezone=processed.user_timezone,
        reference_date=processed.reference_date,
        processing_metadata={
            "removed_sections": processed.removed_sections,
            "processor_version": "email-processing-v1",
        },
        received_at=internal_date,
        sent_at=sent_at,
        labels=labels,
        is_read="UNREAD" not in labels,
        is_starred="STARRED" in labels,
        raw_metadata={
            "size_estimate": payload.get("sizeEstimate"),
            "history_id": payload.get("historyId"),
        },
        attachments=attachments,
    )


class GmailSyncService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.oauth = GoogleOAuthService(settings)
        self._semaphore = asyncio.Semaphore(settings.gmail_sync_concurrency)

    async def _request(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        async with self._semaphore:
            for attempt in range(self.settings.gmail_sync_max_retries):
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if response.status_code not in {429, 500, 502, 503, 504}:
                    return response
                if attempt + 1 < self.settings.gmail_sync_max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
            return response

    async def _recent_message_ids(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        limit: int,
    ) -> list[str]:
        response = await self._request(
            client,
            f"{GMAIL_API_BASE}/messages",
            access_token=access_token,
            params={"maxResults": limit},
        )
        self._raise_for_gmail(response, "GMAIL_LIST_FAILED")
        return [item["id"] for item in response.json().get("messages", [])][:limit]

    async def _incremental_message_ids(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        history_id: str,
        limit: int,
    ) -> list[str] | None:
        response = await self._request(
            client,
            f"{GMAIL_API_BASE}/history",
            access_token=access_token,
            params={
                "startHistoryId": history_id,
                "historyTypes": "messageAdded",
                "maxResults": limit,
            },
        )
        if response.status_code == 404:
            return None
        self._raise_for_gmail(response, "GMAIL_HISTORY_FAILED")
        ids: list[str] = []
        for history in response.json().get("history", []):
            for added in history.get("messagesAdded", []):
                message_id = added.get("message", {}).get("id")
                if message_id and message_id not in ids:
                    ids.append(message_id)
        return ids[:limit]

    async def _fetch_message(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        message_id: str,
    ) -> dict[str, Any] | None:
        response = await self._request(
            client,
            f"{GMAIL_API_BASE}/messages/{message_id}",
            access_token=access_token,
            params={"format": "full"},
        )
        if response.status_code == 404:
            return None
        self._raise_for_gmail(response, "GMAIL_MESSAGE_FAILED")
        return response.json()

    async def _process_attachments(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        message: ParsedGmailMessage,
    ) -> ParsedGmailMessage:
        processed: list[ParsedAttachment] = []
        for index, attachment in enumerate(message.attachments):
            if attachment.is_inline:
                processed.append(replace(attachment, extraction_status="inline_skipped"))
                continue
            if index >= self.settings.attachment_max_per_email:
                processed.append(
                    replace(
                        attachment,
                        extraction_status="limit_skipped",
                        extraction_error="attachment_count_limit",
                    )
                )
                continue
            if attachment.mime_type not in ALLOWED_ATTACHMENT_TYPES:
                processed.append(
                    replace(
                        attachment,
                        extraction_status="unsupported",
                        extraction_error="attachment_type_not_allowed",
                    )
                )
                continue
            if (
                attachment.size_bytes is not None
                and attachment.size_bytes > self.settings.attachment_max_size_bytes
            ):
                processed.append(
                    replace(
                        attachment,
                        extraction_status="too_large",
                        extraction_error="attachment_size_limit",
                    )
                )
                continue

            response = await self._request(
                client,
                f"{GMAIL_API_BASE}/messages/{message.provider_message_id}/attachments/"
                f"{attachment.provider_attachment_id}",
                access_token=access_token,
            )
            if response.is_error:
                processed.append(
                    replace(
                        attachment,
                        extraction_status="failed",
                        extraction_error=f"gmail_attachment_http_{response.status_code}",
                    )
                )
                continue
            content = _decode_base64url_bytes(response.json().get("data"))
            extraction = extract_attachment_text(
                content=content,
                filename=attachment.filename,
                mime_type=attachment.mime_type,
                max_size_bytes=self.settings.attachment_max_size_bytes,
            )
            processed.append(
                replace(
                    attachment,
                    extraction_status=extraction.status,
                    extracted_text=extraction.extracted_text,
                    extraction_error=extraction.error,
                )
            )
        return replace(message, attachments=processed)

    async def sync(
        self, db: Session, account: EmailAccount, *, limit: int
    ) -> GmailSyncResult:
        if account.provider != "google" or account.oauth_credential is None:
            raise AppError(
                code="GMAIL_ACCOUNT_NOT_CONNECTED",
                message="A connected Gmail account is required.",
                status_code=409,
            )
        limit = min(max(limit, 1), self.settings.gmail_sync_limit)
        account.sync_status = "syncing"
        db.commit()

        try:
            access_token = await self.oauth.valid_access_token(
                db, account.oauth_credential
            )
            previous_history_id = account.provider_metadata.get("history_id")
            mode = "full"
            async with httpx.AsyncClient(timeout=30) as client:
                message_ids: list[str] | None = None
                if account.last_synced_at and previous_history_id:
                    message_ids = await self._incremental_message_ids(
                        client, access_token, str(previous_history_id), limit
                    )
                    if message_ids is not None:
                        mode = "incremental"
                if message_ids is None:
                    message_ids = await self._recent_message_ids(
                        client, access_token, limit
                    )

                raw_messages = await asyncio.gather(
                    *[
                        self._fetch_message(client, access_token, message_id)
                        for message_id in message_ids
                    ],
                    return_exceptions=True,
                )
                profile_response = await self._request(
                    client,
                    f"{GMAIL_API_BASE}/profile",
                    access_token=access_token,
                )
                self._raise_for_gmail(profile_response, "GMAIL_PROFILE_FAILED")
                latest_history_id = profile_response.json().get("historyId")

            created = updated = skipped = failed = 0
            parsed_messages: list[ParsedGmailMessage] = []
            user_timezone = db.scalar(
                select(UserPreference.timezone).where(
                    UserPreference.user_id == account.user_id
                )
            ) or self.settings.email_user_timezone
            for raw in raw_messages:
                if isinstance(raw, Exception):
                    failed += 1
                elif raw is None:
                    skipped += 1
                else:
                    try:
                        parsed_messages.append(
                            parse_gmail_message(
                                raw, user_timezone=user_timezone
                            )
                        )
                    except (KeyError, TypeError, ValueError):
                        failed += 1

            async with httpx.AsyncClient(timeout=30) as attachment_client:
                attachment_results = await asyncio.gather(
                    *[
                        self._process_attachments(
                            attachment_client, access_token, parsed
                        )
                        for parsed in parsed_messages
                    ],
                    return_exceptions=True,
                )
            parsed_messages = [
                result if isinstance(result, ParsedGmailMessage) else original
                for original, result in zip(
                    parsed_messages, attachment_results, strict=True
                )
            ]

            for parsed in parsed_messages:
                was_created = self._upsert_message(db, account, parsed)
                created += int(was_created)
                updated += int(not was_created)

            account.last_synced_at = datetime.now(UTC)
            account.sync_status = "connected"
            # Keep the old cursor when any message failed. The next incremental
            # run will see the same Gmail history window and retry that message.
            saved_history_id = (
                latest_history_id if failed == 0 else previous_history_id
            )
            account.provider_metadata = {
                **account.provider_metadata,
                "history_id": saved_history_id,
                "last_sync_mode": mode,
                "last_sync_requested": len(message_ids),
                "last_sync_failed": failed,
            }
            db.commit()
            return GmailSyncResult(
                account_id=str(account.id),
                requested=len(message_ids),
                fetched=len(parsed_messages),
                created=created,
                updated=updated,
                skipped=skipped,
                failed=failed,
                mode=mode,
                history_id=str(saved_history_id) if saved_history_id else None,
            )
        except Exception as exc:
            db.rollback()
            persisted_account = db.get(EmailAccount, account.id)
            if persisted_account is not None:
                persisted_account.sync_status = "error"
                persisted_account.provider_metadata = {
                    **persisted_account.provider_metadata,
                    "last_sync_error": type(exc).__name__,
                    "last_sync_failed_at": datetime.now(UTC).isoformat(),
                }
                db.commit()
            raise

    def _upsert_message(
        self,
        db: Session,
        account: EmailAccount,
        parsed: ParsedGmailMessage,
    ) -> bool:
        thread = db.scalar(
            select(EmailThread).where(
                EmailThread.email_account_id == account.id,
                EmailThread.provider_thread_id == parsed.provider_thread_id,
            )
        )
        if thread is None:
            thread = EmailThread(
                email_account_id=account.id,
                provider_thread_id=parsed.provider_thread_id,
                subject=parsed.subject,
                snippet=parsed.snippet,
                participants=[parsed.sender]
                + parsed.recipients.get("to", [])
                + parsed.recipients.get("cc", []),
                latest_message_at=parsed.received_at,
                message_count=0,
            )
            db.add(thread)
            db.flush()

        email = db.scalar(
            select(Email).where(
                Email.email_account_id == account.id,
                Email.provider_message_id == parsed.provider_message_id,
            )
        )
        created = email is None
        if email is None:
            email = Email(
                email_account_id=account.id,
                provider_message_id=parsed.provider_message_id,
                received_at=parsed.received_at,
            )
            db.add(email)
            db.flush()

        email.thread_id = thread.id
        email.internet_message_id = parsed.internet_message_id
        email.sender = parsed.sender
        email.recipients = parsed.recipients
        email.subject = parsed.subject
        email.snippet = parsed.snippet
        email.body_text = parsed.body_text
        email.body_html = parsed.body_html
        email.raw_body_html = parsed.raw_body_html
        email.cleaned_text = parsed.cleaned_text
        email.original_timezone = parsed.original_timezone
        email.user_timezone = parsed.user_timezone
        email.reference_date = parsed.reference_date
        email.processing_metadata = parsed.processing_metadata
        email.received_at = parsed.received_at
        email.sent_at = parsed.sent_at
        email.labels = parsed.labels
        email.is_read = parsed.is_read
        email.is_starred = parsed.is_starred
        email.raw_metadata = parsed.raw_metadata

        existing_attachment_ids = {item.provider_attachment_id for item in email.attachments}
        for item in parsed.attachments:
            if item.provider_attachment_id not in existing_attachment_ids:
                email.attachments.append(
                    Attachment(
                        provider_attachment_id=item.provider_attachment_id,
                        filename=item.filename,
                        mime_type=item.mime_type,
                        size_bytes=item.size_bytes,
                        content_id=item.content_id,
                        is_inline=item.is_inline,
                        extraction_status=item.extraction_status,
                        extracted_text=item.extracted_text,
                        extraction_error=item.extraction_error,
                    )
                )
            else:
                existing = next(
                    attachment
                    for attachment in email.attachments
                    if attachment.provider_attachment_id
                    == item.provider_attachment_id
                )
                existing.extraction_status = item.extraction_status
                existing.extracted_text = item.extracted_text
                existing.extraction_error = item.extraction_error

        thread.subject = parsed.subject or thread.subject
        thread.snippet = parsed.snippet or thread.snippet
        if not thread.latest_message_at or parsed.received_at >= thread.latest_message_at:
            thread.latest_message_at = parsed.received_at
        db.flush()
        thread.message_count = db.scalar(
            select(func.count(Email.id)).where(Email.thread_id == thread.id)
        ) or 0
        return created

    @staticmethod
    def _raise_for_gmail(response: httpx.Response, code: str) -> None:
        if response.is_error:
            raise AppError(
                code=code,
                message="Gmail synchronization failed. Please retry.",
                status_code=502,
                details={"gmail_status": response.status_code},
            )
