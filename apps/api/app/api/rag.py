from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.db.models.email import Email
from app.db.models.identity import EmailAccount
from app.schemas.rag import (
    MailboxRagSearchRequest,
    RagIndexResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.services.rag import EmbeddingClient, RagService


router = APIRouter(prefix="/rag", tags=["rag"])


def get_rag_service(settings: Settings = Depends(get_settings)) -> RagService:
    return RagService(settings, EmbeddingClient(settings))


def verify_tool_key(
    x_rag_tool_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.rag_tool_api_key and x_rag_tool_key != settings.rag_tool_api_key:
        raise AppError(
            code="RAG_TOOL_UNAUTHORIZED",
            message="The RAG tool credential is invalid.",
            status_code=401,
        )


@router.post(
    "/users/{user_id}/emails/{email_id}/index",
    response_model=RagIndexResponse,
    summary="Chunk and embed one owned email",
)
async def index_email(
    user_id: UUID,
    email_id: UUID,
    db: Session = Depends(get_db),
    service: RagService = Depends(get_rag_service),
) -> RagIndexResponse:
    result = await service.index_email(db, user_id=user_id, email_id=email_id)
    settings = get_settings()
    return RagIndexResponse(
        email_id=result.email_id,
        chunks_created=result.chunks_created,
        embedding_model=(
            "deterministic-test-vector"
            if settings.rag_embedding_mock_mode
            else settings.dify_embedding_model
        ),
    )


@router.post(
    "/search",
    response_model=RagSearchResponse,
    dependencies=[Depends(verify_tool_key)],
    summary="Retrieve owned email evidence for the Dify RAG tool",
)
async def search_email_history(
    request: RagSearchRequest,
    db: Session = Depends(get_db),
    service: RagService = Depends(get_rag_service),
) -> RagSearchResponse:
    return await service.search(db, request)


@router.post(
    "/emails/{email_id}/search",
    response_model=RagSearchResponse,
    summary="Search email history from the MailPilot inbox",
)
async def search_from_mailbox(
    email_id: UUID,
    request: MailboxRagSearchRequest,
    db: Session = Depends(get_db),
    service: RagService = Depends(get_rag_service),
) -> RagSearchResponse:
    """V1 browser route scoped to the currently connected Gmail mailbox."""
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
    return await service.search(
        db,
        RagSearchRequest(
            user_id=account.user_id,
            query=request.query,
            scope=request.scope,
            email_id=email.id,
            thread_id=email.thread_id,
            sender=service._sender_text(email.sender),
            top_k=request.top_k,
        ),
    )
