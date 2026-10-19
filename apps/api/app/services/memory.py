from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.productivity import Memory, UserPreference
from app.schemas.memory import (
    EpisodicMemoryCreate,
    EpisodicMemoryResponse,
    ReplyPreviewResponse,
    UserPreferencesResponse,
    UserPreferencesToolResponse,
    UserPreferencesUpdate,
)


DEFAULT_SETTINGS: dict[str, Any] = {
    "reply_tone": "professional",
    "working_hours_start": "09:00",
    "working_hours_end": "18:00",
    "working_days": [1, 2, 3, 4, 5],
    "meeting_duration_minutes": 30,
    "email_signature": "",
    "important_contacts": [],
    "long_term_memory_enabled": True,
}


def get_or_create_preferences(db: Session, user_id: UUID) -> UserPreference:
    preference = db.scalar(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    if preference is None:
        preference = UserPreference(
            user_id=user_id,
            locale="zh-CN",
            timezone="Asia/Singapore",
            translation_language="zh-CN",
            settings=dict(DEFAULT_SETTINGS),
        )
        db.add(preference)
        db.flush()
    return preference


def preference_payload(preference: UserPreference) -> UserPreferencesUpdate:
    settings = {**DEFAULT_SETTINGS, **(preference.settings or {})}
    return UserPreferencesUpdate(
        default_language=preference.locale,
        translation_language=preference.translation_language or preference.locale,
        timezone=preference.timezone,
        auto_translate=preference.auto_translate,
        **settings,
    )


def preference_response(preference: UserPreference) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        id=preference.id,
        updated_at=preference.updated_at,
        **preference_payload(preference).model_dump(),
    )


def update_preferences(
    db: Session, user_id: UUID, data: UserPreferencesUpdate
) -> UserPreference:
    preference = get_or_create_preferences(db, user_id)
    preference.locale = data.default_language
    preference.translation_language = data.translation_language
    preference.timezone = data.timezone
    preference.auto_translate = data.auto_translate
    preference.settings = data.model_dump(
        exclude={"default_language", "translation_language", "timezone", "auto_translate"}
    )
    db.flush()
    return preference


def create_episode(db: Session, user_id: UUID, data: EpisodicMemoryCreate) -> Memory:
    memory = Memory(
        user_id=user_id,
        source_email_id=data.source_email_id,
        scope="episodic",
        kind="suggestion_feedback",
        content={
            "decision": data.decision,
            "suggestion_type": data.suggestion_type,
            "summary": data.summary,
            "is_email_fact": False,
        },
    )
    db.add(memory)
    db.flush()
    return memory


def episode_response(memory: Memory) -> EpisodicMemoryResponse:
    return EpisodicMemoryResponse(
        id=memory.id,
        decision=memory.content["decision"],
        suggestion_type=memory.content["suggestion_type"],
        summary=memory.content["summary"],
        source_email_id=memory.source_email_id,
        is_active=memory.is_active,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
        is_email_fact=False,
    )


def get_user_preferences_tool(
    db: Session, user_id: UUID
) -> UserPreferencesToolResponse:
    preference = get_or_create_preferences(db, user_id)
    payload = preference_payload(preference)
    memories: list[EpisodicMemoryResponse] = []
    if payload.long_term_memory_enabled:
        rows = db.scalars(
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.scope == "episodic",
                Memory.kind == "suggestion_feedback",
                Memory.is_active.is_(True),
            )
            .order_by(Memory.created_at.desc())
            .limit(20)
        ).all()
        memories = [episode_response(row) for row in rows]
    return UserPreferencesToolResponse(
        preferences=payload,
        episodic_guidance=memories,
    )


def create_reply_preview(
    preferences: UserPreferencesUpdate, recipient_name: str, purpose: str
) -> ReplyPreviewResponse:
    openings = {
        "professional": f"Dear {recipient_name},\n\nThank you for your email.",
        "friendly": f"Hi {recipient_name},\n\nThanks for reaching out!",
        "concise": f"Hi {recipient_name},",
        "formal": f"Dear {recipient_name},\n\nThank you for your correspondence.",
    }
    closings = {
        "professional": "Kind regards,",
        "friendly": "Best,",
        "concise": "Regards,",
        "formal": "Yours sincerely,",
    }
    signature = preferences.email_signature.strip()
    body = f"{openings[preferences.reply_tone]}\n\n{purpose}\n\n{closings[preferences.reply_tone]}"
    if signature:
        body = f"{body}\n{signature}"
    return ReplyPreviewResponse(
        tone=preferences.reply_tone,
        subject="Re: Follow-up",
        body=body,
    )
