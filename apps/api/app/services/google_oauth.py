from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

import httpx
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.crypto import TokenCipher
from app.core.errors import AppError
from app.db.models.identity import EmailAccount, OAuthCredential, User


GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


@dataclass(frozen=True)
class GoogleTokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    token_type: str | None
    scopes: list[str]


class OAuthStateManager:
    def __init__(self, secret: str, max_age_seconds: int) -> None:
        if not secret:
            raise AppError(
                code="OAUTH_NOT_CONFIGURED",
                message="OAuth state signing is not configured.",
                status_code=503,
            )
        self._serializer = URLSafeTimedSerializer(secret, salt="mailpilot-google-oauth")
        self._max_age_seconds = max_age_seconds

    def create(self, user_id: UUID) -> str:
        return self._serializer.dumps({"user_id": str(user_id)})

    def verify(self, state: str) -> UUID:
        try:
            payload = self._serializer.loads(state, max_age=self._max_age_seconds)
            return UUID(payload["user_id"])
        except SignatureExpired as exc:
            raise AppError(
                code="OAUTH_STATE_EXPIRED",
                message="The Google connection request expired. Please try again.",
                status_code=400,
            ) from exc
        except (BadSignature, KeyError, TypeError, ValueError) as exc:
            raise AppError(
                code="OAUTH_STATE_INVALID",
                message="The Google connection request is invalid.",
                status_code=400,
            ) from exc


class GoogleOAuthService:
    def __init__(self, settings: Settings) -> None:
        if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
            raise AppError(
                code="OAUTH_NOT_CONFIGURED",
                message="Google OAuth client credentials are not configured.",
                status_code=503,
            )
        self.settings = settings
        self.state = OAuthStateManager(
            settings.oauth_state_secret, settings.oauth_state_max_age_seconds
        )
        self.cipher = TokenCipher(settings.token_encryption_key)

    def authorization_url(self, user_id: UUID) -> str:
        params = {
            "client_id": self.settings.google_oauth_client_id,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.settings.google_oauth_scopes),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": self.state.create(user_id),
        }
        return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> GoogleTokenSet:
        payload = {
            "code": code,
            "client_id": self.settings.google_oauth_client_id,
            "client_secret": self.settings.google_oauth_client_secret,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if response.is_error:
            raise AppError(
                code="OAUTH_CODE_EXCHANGE_FAILED",
                message="Google could not complete the account connection.",
                status_code=400,
            )
        return self._parse_token_response(response.json())

    async def gmail_profile(self, access_token: str) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                GMAIL_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.is_error:
            raise AppError(
                code="GMAIL_PROFILE_FAILED",
                message="MailPilot could not read the connected Gmail profile.",
                status_code=400,
            )
        return response.json()

    def save_connection(
        self,
        db: Session,
        *,
        user_id: UUID,
        profile: dict[str, str],
        tokens: GoogleTokenSet,
    ) -> EmailAccount:
        user = db.get(User, user_id)
        if user is None:
            raise AppError(
                code="USER_NOT_FOUND", message="User was not found.", status_code=404
            )

        email_address = profile["emailAddress"]
        provider_account_id = email_address.lower()
        account = db.scalar(
            select(EmailAccount).where(
                EmailAccount.provider == "google",
                EmailAccount.provider_account_id == provider_account_id,
            )
        )
        if account is None:
            account = EmailAccount(
                user_id=user_id,
                provider="google",
                provider_account_id=provider_account_id,
                email_address=email_address,
                sync_status="connected",
                scopes=tokens.scopes,
                provider_metadata={"history_id": profile.get("historyId")},
            )
            db.add(account)
            db.flush()
        else:
            account.user_id = user_id
            account.email_address = email_address
            account.sync_status = "connected"
            account.scopes = tokens.scopes
            account.provider_metadata = {"history_id": profile.get("historyId")}

        credential = account.oauth_credential
        if credential is None:
            credential = OAuthCredential(
                email_account_id=account.id,
                access_token_ciphertext="",
                key_version=self.settings.token_encryption_key_version,
            )
            db.add(credential)
        credential.access_token_ciphertext = self.cipher.encrypt(tokens.access_token)
        if tokens.refresh_token:
            credential.refresh_token_ciphertext = self.cipher.encrypt(
                tokens.refresh_token
            )
        credential.expires_at = tokens.expires_at
        credential.token_type = tokens.token_type
        credential.scopes = tokens.scopes
        credential.key_version = self.settings.token_encryption_key_version
        db.commit()
        db.refresh(account)
        return account

    async def valid_access_token(
        self, db: Session, credential: OAuthCredential
    ) -> str:
        now = datetime.now(UTC)
        if credential.expires_at and credential.expires_at > now + timedelta(seconds=60):
            return self.cipher.decrypt(credential.access_token_ciphertext)
        if not credential.refresh_token_ciphertext:
            raise AppError(
                code="OAUTH_RECONNECT_REQUIRED",
                message="Google access expired. Please reconnect the account.",
                status_code=401,
            )

        refresh_token = self.cipher.decrypt(credential.refresh_token_ciphertext)
        payload = {
            "client_id": self.settings.google_oauth_client_id,
            "client_secret": self.settings.google_oauth_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if response.is_error:
            raise AppError(
                code="OAUTH_REFRESH_FAILED",
                message="Google access could not be refreshed. Please reconnect.",
                status_code=401,
            )
        refreshed = self._parse_token_response(response.json())
        credential.access_token_ciphertext = self.cipher.encrypt(refreshed.access_token)
        credential.expires_at = refreshed.expires_at
        credential.token_type = refreshed.token_type
        if refreshed.scopes:
            credential.scopes = refreshed.scopes
        db.commit()
        return refreshed.access_token

    async def disconnect(self, db: Session, account: EmailAccount) -> None:
        credential = account.oauth_credential
        if credential is not None:
            token_ciphertext = (
                credential.refresh_token_ciphertext
                or credential.access_token_ciphertext
            )
            token = self.cipher.decrypt(token_ciphertext)
            async with httpx.AsyncClient(timeout=15) as client:
                await client.post(GOOGLE_REVOKE_URL, data={"token": token})
            db.delete(credential)
        account.sync_status = "disconnected"
        account.scopes = []
        db.commit()

    @staticmethod
    def _parse_token_response(payload: dict) -> GoogleTokenSet:
        expires_in = payload.get("expires_in")
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=int(expires_in))
            if expires_in is not None
            else None
        )
        raw_scope = payload.get("scope", "")
        return GoogleTokenSet(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=expires_at,
            token_type=payload.get("token_type"),
            scopes=raw_scope.split() if raw_scope else [],
        )
