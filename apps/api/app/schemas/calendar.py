from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CalendarModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: value.split("_")[0]
        + "".join(part.capitalize() for part in value.split("_")[1:]),
        populate_by_name=True,
    )


class CalendarEventInput(CalendarModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    starts_at: datetime
    ends_at: datetime | None = None
    timezone: str = Field(default="Asia/Singapore", max_length=64)
    location: str | None = Field(default=None, max_length=500)
    attendees: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("calendar times must include a timezone")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def valid_time_range(self) -> "CalendarEventInput":
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class CalendarEventUpdate(CalendarModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=500)
    attendees: list[str] | None = Field(default=None, max_length=50)

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("calendar times must include a timezone")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value


class CalendarEventResponse(CalendarModel):
    id: UUID
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    location: str | None
    attendees: list[str] = Field(default_factory=list)
    status: Literal[
        "needs_clarification",
        "pending_approval",
        "executing",
        "confirmed",
        "verification_failed",
        "rejected",
    ]
    source: Literal["email", "manual"]
    email_id: UUID | None
    evidence: str | None
    created_at: datetime
    approval_id: UUID | None = None
    approval_payload_hash: str | None = None
    approval_expires_at: datetime | None = None
    provider_event_id: str | None = None
    verified: bool = False


class ApprovalDecisionRequest(CalendarModel):
    approval_id: UUID
    payload_hash: str = Field(min_length=64, max_length=64)


class CalendarAvailabilityInput(CalendarModel):
    starts_at: datetime
    ends_at: datetime

    @model_validator(mode="after")
    def valid_range(self) -> "CalendarAvailabilityInput":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("calendar times must include a timezone")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class CalendarAvailabilityResponse(CalendarModel):
    available: bool
    busy: list[dict] = Field(default_factory=list)


class CalendarOverviewResponse(CalendarModel):
    events: list[CalendarEventResponse]
    candidates: list[CalendarEventResponse]
