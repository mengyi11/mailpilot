from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.schemas.structured_output import (
    EmailAnalysis,
    EmailCategory,
    EmailPriority,
)
from app.services.dify_client import DifyAPIError, DifyConfigurationError


CATEGORY_ALIASES = {
    "work": EmailCategory.WORK,
    "study": EmailCategory.STUDY,
    "finance": EmailCategory.FINANCE,
    "event": EmailCategory.EVENT,
    "notification": EmailCategory.NOTIFICATION,
    "marketing": EmailCategory.MARKETING,
    "personal": EmailCategory.PERSONAL,
    "spam": EmailCategory.SPAM,
    "other": EmailCategory.NOTIFICATION,
    "其他": EmailCategory.NOTIFICATION,
}


def decode_json_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise TypeError("analysis output must be an object or JSON string")
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise TypeError("analysis JSON must decode to an object")
    return payload


def _confidence(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if 0 <= parsed <= 1 else None


def _evidence(value: Any, confidence: float | None) -> dict[str, Any] | None:
    if isinstance(value, dict):
        text = str(value.get("text") or "").strip()
        source = value.get("source") or "email_body"
        evidence_confidence = _confidence(value.get("confidence"))
    else:
        text = str(value or "").strip()
        source = "email_body"
        evidence_confidence = confidence
    if not text or source not in {"subject", "email_body", "attachment"}:
        return None
    return {
        "text": text,
        "source": source,
        "confidence": evidence_confidence if evidence_confidence is not None else 0.5,
    }


def _aware_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


def repair_analysis_payload(
    payload: dict[str, Any],
    *,
    expected_email_id: UUID,
) -> EmailAnalysis:
    supplied_email_id = payload.get("email_id") or payload.get("emailId")
    if supplied_email_id is not None:
        try:
            if UUID(str(supplied_email_id)) != expected_email_id:
                raise ValueError("email_id does not match the requested email")
        except (TypeError, ValueError) as exc:
            raise ValueError("email_id does not match the requested email") from exc
    category_raw = str(payload.get("category") or "通知").strip()
    try:
        category = EmailCategory(category_raw)
    except ValueError:
        category = CATEGORY_ALIASES.get(
            category_raw.lower(), EmailCategory.NOTIFICATION
        )
    priority_raw = str(payload.get("priority") or "normal").lower()
    try:
        priority = EmailPriority(priority_raw)
    except ValueError:
        priority = EmailPriority.NORMAL

    repaired_actions: list[dict[str, Any]] = []
    for item in payload.get("actions") or []:
        if not isinstance(item, dict):
            continue
        confidence = _confidence(item.get("confidence"))
        evidence = _evidence(item.get("evidence"), confidence)
        title = str(item.get("title") or "").strip()
        if not title or confidence is None or evidence is None:
            continue
        due_at = _aware_datetime(item.get("due_at") or item.get("dueAt"))
        repaired_actions.append(
            {
                "title": title,
                "description": item.get("description"),
                "due_at": due_at,
                "evidence": evidence,
                "confidence": confidence,
            }
        )

    repaired_dates: list[dict[str, Any]] = []
    raw_dates = payload.get("extracted_dates") or payload.get("calendar_candidates") or []
    for item in raw_dates:
        if not isinstance(item, dict):
            continue
        start = _aware_datetime(item.get("start"))
        confidence = _confidence(item.get("confidence"))
        evidence = _evidence(item.get("evidence"), confidence)
        timezone = str(item.get("timezone") or "").strip()
        title = str(item.get("title") or "").strip()
        try:
            timezone_info = ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError):
            continue
        if not start or not title or confidence is None or evidence is None:
            continue
        if start.utcoffset() != start.astimezone(timezone_info).utcoffset():
            continue
        end = _aware_datetime(item.get("end"))
        if end is not None and end <= start:
            end = None
        if end is not None and (
            end.utcoffset() != end.astimezone(timezone_info).utcoffset()
        ):
            end = None
        repaired_dates.append(
            {
                "title": title,
                "start": start,
                "end": end,
                "timezone": timezone,
                "location": item.get("location"),
                "description": item.get("description"),
                "attendees": [
                    str(value).strip()
                    for value in (item.get("attendees") or [])
                    if str(value).strip()
                ][:50],
                "evidence": evidence,
                "confidence": confidence,
            }
        )

    top_evidence = [
        evidence
        for item in payload.get("evidence") or []
        if (evidence := _evidence(item, _confidence(getattr(item, "confidence", None))))
    ]
    summary = str(payload.get("summary") or "").strip()
    if not summary:
        raise ValueError("summary is required for schema repair")
    repaired = {
        "email_id": expected_email_id,
        "category": category,
        "priority": priority,
        "summary": summary,
        "translation_needed": bool(payload.get("translation_needed", False)),
        "evidence": top_evidence,
        "actions": repaired_actions,
        "extracted_dates": repaired_dates,
    }
    return EmailAnalysis.model_validate(repaired)


class StrongModelRepairClient:
    """Calls a separate Dify workflow only after deterministic repair fails."""

    def __init__(self, settings: Any, *, http_client: Any = None) -> None:
        self.settings = settings
        self._http_client = http_client

    async def repair(
        self, *, email_id: UUID, raw_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        import httpx

        if self.settings.dify_mock_mode:
            raise DifyConfigurationError("Strong-model repair is disabled in mock mode")
        if not self.settings.dify_repair_api_key:
            raise DifyConfigurationError("DIFY_REPAIR_API_KEY is missing")
        payload = {
            "inputs": {
                "email_id": str(email_id),
                "raw_analysis": json.dumps(raw_analysis, ensure_ascii=False),
            },
            "response_mode": "blocking",
            "user": "mailpilot-schema-repair",
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_repair_api_key}",
            "Content-Type": "application/json",
        }
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=60.0)
        try:
            response = await client.post(
                f"{self.settings.dify_base_url.rstrip('/')}/workflows/run",
                headers=headers,
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise DifyAPIError("Strong-model schema repair request failed") from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.is_error:
            raise DifyAPIError(f"Strong-model schema repair returned HTTP {response.status_code}")
        try:
            body = response.json()
            if body["data"]["status"] != "succeeded":
                raise DifyAPIError(body["data"].get("error") or "Schema repair failed")
            outputs = body["data"]["outputs"]
            return decode_json_payload(outputs["analysis"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise DifyAPIError("Strong-model schema repair returned invalid data") from exc


def safe_read_only_analysis(
    *,
    email_id: UUID,
    payload: dict[str, Any] | None,
) -> EmailAnalysis:
    summary = str((payload or {}).get("summary") or "AI analysis could not be validated.")
    return EmailAnalysis(
        email_id=email_id,
        category=EmailCategory.NOTIFICATION,
        priority=EmailPriority.NORMAL,
        summary=summary[:4000],
        translation_needed=False,
        evidence=[],
        actions=[],
        extracted_dates=[],
    )

