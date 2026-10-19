from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.memory import UserPreferencesUpdate
from app.services.memory import create_reply_preview, preference_payload


def test_preferences_validate_timezone_and_working_window() -> None:
    with pytest.raises(ValidationError):
        UserPreferencesUpdate(timezone="Mars/Olympus_Mons")
    with pytest.raises(ValidationError):
        UserPreferencesUpdate(working_hours_start="18:00", working_hours_end="09:00")


def test_reply_tone_and_signature_change_new_draft() -> None:
    professional = UserPreferencesUpdate(
        reply_tone="professional", email_signature="Mengyi"
    )
    friendly = UserPreferencesUpdate(reply_tone="friendly", email_signature="M")

    first = create_reply_preview(professional, "Alex", "I will review it.")
    second = create_reply_preview(friendly, "Alex", "I will review it.")

    assert first.body != second.body
    assert "Dear Alex" in first.body
    assert "Hi Alex" in second.body
    assert first.body.endswith("Mengyi")


def test_preference_payload_merges_safe_defaults() -> None:
    preference = SimpleNamespace(
        id=uuid4(),
        locale="en",
        translation_language=None,
        timezone="UTC",
        auto_translate=False,
        settings={"reply_tone": "concise", "long_term_memory_enabled": False},
    )

    payload = preference_payload(preference)

    assert payload.reply_tone == "concise"
    assert payload.translation_language == "en"
    assert payload.meeting_duration_minutes == 30
    assert payload.long_term_memory_enabled is False
