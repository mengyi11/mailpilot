from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from app.db.models.agent import Approval


APPROVAL_TTL = timedelta(hours=24)


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def calendar_payload(draft) -> dict[str, Any]:
    return {
        "draft_id": str(draft.id),
        "title": draft.title,
        "description": draft.description,
        "starts_at": draft.starts_at.isoformat(),
        "ends_at": draft.ends_at.isoformat() if draft.ends_at else None,
        "timezone": draft.timezone,
        "location": draft.location,
        "attendees": draft.attendees,
    }


def new_calendar_approval(*, draft, user_id, agent_run_id=None) -> Approval:
    payload = calendar_payload(draft)
    now = datetime.now(UTC)
    return Approval(
        user_id=user_id,
        agent_run_id=agent_run_id,
        action="create_calendar_event",
        resource_type="calendar_draft",
        resource_id=draft.id,
        proposed_payload=payload,
        payload_hash=canonical_payload_hash(payload),
        status="pending",
        requested_at=now,
        expires_at=now + APPROVAL_TTL,
    )
