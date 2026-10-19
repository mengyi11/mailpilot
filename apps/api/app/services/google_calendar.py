from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models.identity import EmailAccount
from app.services.google_oauth import GoogleOAuthService


CALENDAR_API = "https://www.googleapis.com/calendar/v3"
EVENT_SCOPE = "https://www.googleapis.com/auth/calendar.events"
FREEBUSY_SCOPE = "https://www.googleapis.com/auth/calendar.events.freebusy"


class GoogleCalendarService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.oauth = GoogleOAuthService(settings)

    @staticmethod
    def require_scope(account: EmailAccount, scope: str) -> None:
        if scope not in account.scopes:
            raise AppError(
                code="GOOGLE_CALENDAR_RECONNECT_REQUIRED",
                message="请重新连接 Google 账户并授予日历权限。",
                status_code=409,
            )

    async def _token(self, db, account: EmailAccount) -> str:
        if account.oauth_credential is None:
            raise AppError(
                code="GOOGLE_CALENDAR_NOT_CONNECTED",
                message="Google 账户尚未连接。",
                status_code=409,
            )
        return await self.oauth.valid_access_token(db, account.oauth_credential)

    async def check_availability(
        self, db, account: EmailAccount, *, start: datetime, end: datetime
    ) -> dict[str, Any]:
        self.require_scope(account, FREEBUSY_SCOPE)
        token = await self._token(db, account)
        payload = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": "primary"}],
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{CALENDAR_API}/freeBusy",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
        if response.is_error:
            raise AppError(
                code="CALENDAR_AVAILABILITY_FAILED",
                message="暂时无法查询 Google Calendar 空闲时间。",
                status_code=502,
            )
        busy = response.json().get("calendars", {}).get("primary", {}).get("busy", [])
        return {"available": not busy, "busy": busy}

    async def create_event(
        self,
        db,
        account: EmailAccount,
        *,
        event_id: str,
        payload: dict[str, Any],
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        self.require_scope(account, EVENT_SCOPE)
        token = await self._token(db, account)
        body = self._google_payload(payload, event_id)
        url = f"{CALENDAR_API}/calendars/primary/events"
        async with httpx.AsyncClient(timeout=15) as client:
            for attempt in range(max_attempts):
                response = await client.post(
                    url,
                    params={"sendUpdates": "none"},
                    headers={"Authorization": f"Bearer {token}"},
                    json=body,
                )
                if response.status_code == 409:
                    return await self.get_event(db, account, event_id=event_id)
                if not response.is_error:
                    return response.json()
                if response.status_code not in {429, 500, 502, 503, 504}:
                    break
                if attempt + 1 < max_attempts:
                    await asyncio.sleep(0.25 * (2**attempt))
        raise AppError(
            code="CALENDAR_CREATE_FAILED",
            message="Google Calendar 未能创建事件，请稍后重试。",
            status_code=502,
        )

    async def get_event(
        self, db, account: EmailAccount, *, event_id: str
    ) -> dict[str, Any]:
        self.require_scope(account, EVENT_SCOPE)
        token = await self._token(db, account)
        encoded = quote(event_id, safe="")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{CALENDAR_API}/calendars/primary/events/{encoded}",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.is_error:
            raise AppError(
                code="CALENDAR_EVENT_VERIFICATION_FAILED",
                message="事件已提交，但无法从 Google Calendar 回读验证。",
                status_code=502,
            )
        return response.json()

    @staticmethod
    def _google_payload(payload: dict[str, Any], event_id: str) -> dict[str, Any]:
        start = datetime.fromisoformat(payload["starts_at"])
        end_value = payload.get("ends_at")
        end = datetime.fromisoformat(end_value) if end_value else start + timedelta(hours=1)
        return {
            "id": event_id,
            "summary": payload["title"],
            "description": payload.get("description") or "",
            "location": payload.get("location") or "",
            "start": {"dateTime": start.isoformat(), "timeZone": payload["timezone"]},
            "end": {"dateTime": end.isoformat(), "timeZone": payload["timezone"]},
            "attendees": payload.get("attendees") or [],
            "extendedProperties": {
                "private": {"mailpilotDraftId": payload["draft_id"]}
            },
        }


def verify_event(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    def same_instant(actual_value: str | None, expected_value: str | None) -> bool:
        if expected_value is None:
            return True
        if actual_value is None:
            return False
        return datetime.fromisoformat(actual_value.replace("Z", "+00:00")) == datetime.fromisoformat(expected_value.replace("Z", "+00:00"))

    expected_attendees = sorted(
        item.get("email", "").lower() for item in expected.get("attendees", [])
    )
    actual_attendees = sorted(
        item.get("email", "").lower() for item in actual.get("attendees", [])
    )
    checks = {
        "title": actual.get("summary") == expected["title"],
        "start": same_instant(actual.get("start", {}).get("dateTime"), expected["starts_at"]),
        "end": same_instant(actual.get("end", {}).get("dateTime"), expected.get("ends_at")),
        "timezone": actual.get("start", {}).get("timeZone") == expected["timezone"],
        "attendees": actual_attendees == expected_attendees,
    }
    return {"verified": all(checks.values()), "checks": checks}
