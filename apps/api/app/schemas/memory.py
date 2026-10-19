from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=lambda value: value.split("_")[0] + "".join(
        part.capitalize() for part in value.split("_")[1:]
    ), populate_by_name=True)


class ImportantContact(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    note: str | None = Field(default=None, max_length=240)


class UserPreferencesUpdate(ApiModel):
    default_language: str = Field(default="zh-CN", min_length=2, max_length=16)
    translation_language: str = Field(default="zh-CN", min_length=2, max_length=16)
    timezone: str = Field(default="Asia/Singapore", min_length=1, max_length=64)
    auto_translate: bool = False
    reply_tone: Literal["professional", "friendly", "concise", "formal"] = "professional"
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"
    working_days: list[int] = Field(default=[1, 2, 3, 4, 5], min_length=1)
    meeting_duration_minutes: int = Field(default=30, ge=15, le=180)
    email_signature: str = Field(default="", max_length=2000)
    important_contacts: list[ImportantContact] = Field(default_factory=list, max_length=50)
    long_term_memory_enabled: bool = True

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value

    @field_validator("working_hours_start", "working_hours_end")
    @classmethod
    def validate_clock_time(cls, value: str) -> str:
        try:
            hour, minute = (int(part) for part in value.split(":"))
        except (ValueError, TypeError) as exc:
            raise ValueError("time must use HH:MM") from exc
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("time must use HH:MM")
        return f"{hour:02d}:{minute:02d}"

    @field_validator("working_days")
    @classmethod
    def validate_working_days(cls, value: list[int]) -> list[int]:
        if any(day < 1 or day > 7 for day in value):
            raise ValueError("working days must be between 1 and 7")
        return sorted(set(value))

    @model_validator(mode="after")
    def validate_working_window(self) -> "UserPreferencesUpdate":
        if self.working_hours_start >= self.working_hours_end:
            raise ValueError("working hours end must be later than start")
        return self


class UserPreferencesResponse(UserPreferencesUpdate):
    id: UUID
    updated_at: datetime


class EpisodicMemoryCreate(ApiModel):
    decision: Literal["accepted", "rejected"]
    suggestion_type: str = Field(min_length=1, max_length=64)
    summary: str = Field(min_length=1, max_length=1000)
    source_email_id: UUID | None = None


class EpisodicMemoryUpdate(ApiModel):
    summary: str | None = Field(default=None, min_length=1, max_length=1000)
    is_active: bool | None = None


class EpisodicMemoryResponse(ApiModel):
    id: UUID
    decision: Literal["accepted", "rejected"]
    suggestion_type: str
    summary: str
    source_email_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_email_fact: Literal[False] = False


class ReplyPreviewRequest(ApiModel):
    recipient_name: str = Field(default="Alex", min_length=1, max_length=120)
    purpose: str = Field(default="确认已收到邮件并会尽快回复", min_length=1, max_length=500)


class ReplyPreviewResponse(ApiModel):
    tone: str
    subject: str
    body: str


class SessionRunResponse(ApiModel):
    id: UUID
    workflow_name: str
    status: str
    trace_id: str
    email_id: UUID | None
    steps: int
    tool_calls: int
    approvals: int
    created_at: datetime


class UserPreferencesToolResponse(ApiModel):
    preferences: UserPreferencesUpdate
    episodic_guidance: list[EpisodicMemoryResponse]
    epistemic_scope: Literal["user_preferences_only"] = "user_preferences_only"
    must_not_use_as_email_fact: Literal[True] = True
