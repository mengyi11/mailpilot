from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models.identity import EmailAccount
from app.db.session import get_db
from app.services.google_oauth import GoogleOAuthService


router = APIRouter(prefix="/auth/google", tags=["google-oauth"])


class GoogleConnectResponse(BaseModel):
    authorization_url: str


class GoogleDisconnectResponse(BaseModel):
    status: str
    account_id: UUID


@router.get(
    "/connect",
    response_model=GoogleConnectResponse,
    summary="Start a secure Google OAuth connection",
)
async def connect_google(
    user_id: UUID = Query(description="The signed-in MailPilot user ID."),
) -> GoogleConnectResponse:
    service = GoogleOAuthService(get_settings())
    return GoogleConnectResponse(authorization_url=service.authorization_url(user_id))


@router.get(
    "/callback",
    response_class=RedirectResponse,
    summary="Complete the Google OAuth connection",
)
async def google_callback(
    state: str,
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:
        raise AppError(
            code="OAUTH_ACCESS_DENIED",
            message="Google account access was not granted.",
            status_code=400,
        )
    if not code:
        raise AppError(
            code="OAUTH_CODE_MISSING",
            message="Google did not return an authorization code.",
            status_code=400,
        )

    settings = get_settings()
    service = GoogleOAuthService(settings)
    user_id = service.state.verify(state)
    tokens = await service.exchange_code(code)
    profile = await service.gmail_profile(tokens.access_token)
    account = service.save_connection(
        db, user_id=user_id, profile=profile, tokens=tokens
    )
    destination = f"{settings.frontend_oauth_success_url}?google=connected&account_id={account.id}"
    return RedirectResponse(destination, status_code=303)


@router.post(
    "/accounts/{account_id}/disconnect",
    response_model=GoogleDisconnectResponse,
    summary="Revoke Google access and remove stored OAuth credentials",
)
async def disconnect_google(
    account_id: UUID,
    db: Session = Depends(get_db),
) -> GoogleDisconnectResponse:
    account = db.get(EmailAccount, account_id)
    if account is None or account.provider != "google":
        raise AppError(
            code="GOOGLE_ACCOUNT_NOT_FOUND",
            message="Connected Google account was not found.",
            status_code=404,
        )
    await GoogleOAuthService(get_settings()).disconnect(db, account)
    return GoogleDisconnectResponse(status="disconnected", account_id=account.id)
