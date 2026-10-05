from cryptography.fernet import Fernet, InvalidToken

from app.core.errors import AppError


class TokenCipher:
    """Encrypt OAuth tokens before they cross the database boundary."""

    def __init__(self, key: str) -> None:
        if not key:
            raise AppError(
                code="OAUTH_NOT_CONFIGURED",
                message="Token encryption is not configured.",
                status_code=503,
            )
        try:
            self._fernet = Fernet(key.encode())
        except (TypeError, ValueError) as exc:
            raise AppError(
                code="OAUTH_NOT_CONFIGURED",
                message="Token encryption key is invalid.",
                status_code=503,
            ) from exc

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise AppError(
                code="OAUTH_TOKEN_DECRYPTION_FAILED",
                message="Stored OAuth credentials could not be decrypted.",
                status_code=500,
            ) from exc
