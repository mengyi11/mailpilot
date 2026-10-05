from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.core.crypto import TokenCipher
from app.core.errors import AppError
from app.services.google_oauth import GoogleOAuthService, OAuthStateManager


def test_oauth_state_round_trip_and_tamper_rejection() -> None:
    manager = OAuthStateManager("test-state-secret", 600)
    user_id = uuid4()

    state = manager.create(user_id)

    assert manager.verify(state) == user_id
    with pytest.raises(AppError, match="invalid"):
        manager.verify(f"{state}tampered")


def test_token_cipher_never_stores_plaintext() -> None:
    cipher = TokenCipher(Fernet.generate_key().decode())

    encrypted = cipher.encrypt("refresh-token-value")

    assert encrypted != "refresh-token-value"
    assert cipher.decrypt(encrypted) == "refresh-token-value"


def test_authorization_url_requests_only_backend_scope() -> None:
    settings = Settings(
        google_oauth_client_id="client-id",
        google_oauth_client_secret="client-secret",
        oauth_state_secret="state-secret",
        token_encryption_key=Fernet.generate_key().decode(),
    )
    service = GoogleOAuthService(settings)

    url = service.authorization_url(uuid4())

    assert "accounts.google.com/o/oauth2/v2/auth" in url
    assert "gmail.readonly" in url
    assert "access_type=offline" in url
    assert "client-secret" not in url
