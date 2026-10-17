from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SkillModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class EmailSkillInput(SkillModel):
    email_id: UUID
    subject: str
    sender: str
    sent_at: datetime
    body: str = Field(min_length=1)
    language: str = Field(min_length=2)
    timezone: str = Field(min_length=1)


class TriageOutput(SkillModel):
    category: str = Field(min_length=1, max_length=64)
    priority: Literal["low", "normal", "high"]
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(min_length=1)


class SummarizeOutput(SkillModel):
    summary_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    key_facts: list[str] = Field(default_factory=list, max_length=8)


class TranslateInput(SkillModel):
    text: str = Field(min_length=1)
    source_language: str = Field(min_length=2)
    target_language: Literal["en", "zh-CN"]
    preserve_html: bool = True


class TranslateOutput(SkillModel):
    translated_text: str = Field(min_length=1)
    source_language: str
    target_language: str
    preserved_html: bool


class ActionItem(SkillModel):
    title: str = Field(min_length=1)
    description: str | None = None
    due_at: datetime | None = None
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ActionExtractionOutput(SkillModel):
    actions: list[ActionItem] = Field(default_factory=list)


class ScheduleInput(EmailSkillInput):
    reference_date: datetime


class CalendarCandidate(SkillModel):
    title: str = Field(min_length=1)
    start: datetime
    end: datetime | None = None
    timezone: str = Field(min_length=1)
    location: str | None = None
    evidence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    requires_approval: Literal[True] = True


class ScheduleOutput(SkillModel):
    candidates: list[CalendarCandidate] = Field(default_factory=list)


class ReplyInput(EmailSkillInput):
    intent: str = Field(min_length=1)
    tone: Literal["concise", "friendly", "formal"] = "concise"
    user_preferences: str | None = None


class ReplyOutput(SkillModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    tone: str
    requires_approval: Literal[True] = True

