from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class StructuredModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class EmailCategory(StrEnum):
    WORK = "工作"
    STUDY = "学习"
    FINANCE = "财务"
    EVENT = "活动"
    NOTIFICATION = "通知"
    MARKETING = "营销"
    PERSONAL = "个人"
    SPAM = "垃圾邮件"


class EmailPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Evidence(StructuredModel):
    text: str = Field(min_length=1, max_length=2000)
    source: Literal["subject", "email_body", "attachment"] = "email_body"
    confidence: float = Field(ge=0, le=1)


class ActionItem(StructuredModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    due_at: datetime | None = None
    evidence: Evidence
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_due_at(self) -> "ActionItem":
        if self.due_at is not None and (
            self.due_at.tzinfo is None or self.due_at.utcoffset() is None
        ):
            raise ValueError("due_at must include a UTC offset")
        return self


class ExtractedDate(StructuredModel):
    title: str = Field(min_length=1, max_length=300)
    start: datetime
    end: datetime | None = None
    timezone: str = Field(min_length=1, max_length=64)
    location: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    attendees: list[str] = Field(default_factory=list, max_length=50)
    evidence: Evidence
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_calendar_safety(self) -> "ExtractedDate":
        if self.start.tzinfo is None or self.start.utcoffset() is None:
            raise ValueError("start must include a UTC offset")
        if self.end is not None:
            if self.end.tzinfo is None or self.end.utcoffset() is None:
                raise ValueError("end must include a UTC offset")
            if self.end <= self.start:
                raise ValueError("end must be later than start")
        try:
            timezone = ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        if self.start.utcoffset() != self.start.astimezone(timezone).utcoffset():
            raise ValueError("start UTC offset does not match timezone")
        if self.end is not None and (
            self.end.utcoffset() != self.end.astimezone(timezone).utcoffset()
        ):
            raise ValueError("end UTC offset does not match timezone")
        return self


class EmailAnalysis(StructuredModel):
    email_id: UUID
    category: EmailCategory
    priority: EmailPriority
    summary: str = Field(min_length=1, max_length=4000)
    translation_needed: bool
    evidence: list[Evidence] = Field(default_factory=list, max_length=20)
    actions: list[ActionItem] = Field(default_factory=list, max_length=20)
    extracted_dates: list[ExtractedDate] = Field(default_factory=list, max_length=20)


class CalendarDraft(StructuredModel):
    title: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str
    location: str | None = None
    attendees: list[str] = Field(default_factory=list, max_length=50)
    evidence: Evidence
    confidence: float = Field(ge=0, le=1)
    status: Literal["pending_approval"] = "pending_approval"

    @model_validator(mode="after")
    def validate_calendar_safety(self) -> "CalendarDraft":
        ExtractedDate(
            title=self.title,
            start=self.starts_at,
            end=self.ends_at,
            timezone=self.timezone,
            location=self.location,
            attendees=self.attendees,
            evidence=self.evidence,
            confidence=self.confidence,
        )
        return self


class ReplyDraft(StructuredModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    tone: Literal["concise", "friendly", "formal"]
    language: str = Field(min_length=2)
    evidence: list[Evidence] = Field(default_factory=list)
    requires_approval: Literal[True] = True

