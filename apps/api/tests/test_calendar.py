from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api import calendar as calendar_api
from app.tools import implementations as tool_implementations
from app.core.errors import AppError
from app.db.models.identity import User
from app.db.models.identity import EmailAccount
from app.db.models.productivity import CalendarDraft
from app.schemas.calendar import ApprovalDecisionRequest
from app.services.approval import new_calendar_approval
from app.db.session import engine
from app.schemas.calendar import CalendarEventInput, CalendarEventUpdate


@pytest.fixture
def calendar_db(monkeypatch):
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, expire_on_commit=False)
    owner = User(email=f"calendar-{uuid4()}@example.com", display_name="Calendar Owner")
    stranger = User(email=f"calendar-{uuid4()}@example.com", display_name="Stranger")
    db.add_all([owner, stranger])
    db.flush()
    monkeypatch.setattr(calendar_api, "current_user_id", lambda _db: owner.id)
    yield db, owner, stranger
    db.close()
    transaction.rollback()
    connection.close()


def event_input(title="Manual event"):
    start = datetime(2026, 10, 20, 9, 0, tzinfo=UTC)
    return CalendarEventInput(
        title=title,
        starts_at=start,
        ends_at=start + timedelta(minutes=30),
        timezone="Asia/Singapore",
        location="MailPilot",
    )


def test_calendar_input_rejects_naive_or_reversed_times() -> None:
    with pytest.raises(ValidationError):
        CalendarEventInput(
            title="Invalid",
            starts_at=datetime(2026, 10, 20, 9, 0),
            timezone="Asia/Singapore",
        )
    with pytest.raises(ValidationError):
        CalendarEventInput(
            title="Invalid",
            starts_at=datetime(2026, 10, 20, 10, 0, tzinfo=UTC),
            ends_at=datetime(2026, 10, 20, 9, 0, tzinfo=UTC),
            timezone="Asia/Singapore",
        )


def test_manual_event_create_edit_and_delete(calendar_db) -> None:
    db, _, _ = calendar_db
    created = calendar_api.create_manual_event(event_input(), db)
    assert created.status == "confirmed" and created.source == "manual"

    updated = calendar_api.update_event(
        created.id, CalendarEventUpdate(title="Updated event"), db
    )
    assert updated.title == "Updated event"

    response = calendar_api.delete_event(created.id, db)
    assert response.status_code == 204


@pytest.mark.anyio
async def test_email_candidate_requires_approval(calendar_db, monkeypatch) -> None:
    db, owner, _ = calendar_db
    candidate = CalendarDraft(
        user_id=owner.id,
        status="pending_approval",
        title="Email meeting",
        starts_at=datetime(2026, 10, 21, 2, 0, tzinfo=UTC),
        timezone="Asia/Singapore",
        source_evidence={"text": "Meet on 21 October at 10am"},
    )
    db.add(candidate)
    db.flush()
    account = EmailAccount(
        user_id=owner.id,
        provider="google",
        provider_account_id=f"calendar-{uuid4()}@example.com",
        email_address="calendar@example.com",
        sync_status="connected",
        scopes=[],
        provider_metadata={},
    )
    approval = new_calendar_approval(draft=candidate, user_id=owner.id)
    db.add_all([account, approval])
    db.flush()

    class FakeCalendarService:
        def __init__(self, _settings):
            pass

        async def create_event(self, _db, _account, *, event_id, payload):
            return {"id": event_id}

        async def get_event(self, _db, _account, *, event_id):
            return {
                "id": event_id,
                "summary": candidate.title,
                "start": {
                    "dateTime": candidate.starts_at.isoformat(),
                    "timeZone": candidate.timezone,
                },
                "end": {
                    "dateTime": (candidate.starts_at + timedelta(hours=1)).isoformat(),
                    "timeZone": candidate.timezone,
                },
                "attendees": [],
            }

    monkeypatch.setattr(calendar_api, "GoogleCalendarService", FakeCalendarService)
    monkeypatch.setattr(tool_implementations, "GoogleCalendarService", FakeCalendarService)

    before = calendar_api.calendar_overview(
        starts_from=None, starts_before=None, db=db
    )
    assert [item.id for item in before.candidates] == [candidate.id]
    assert before.events == []

    approved = await calendar_api.approve_candidate(
        candidate.id,
        ApprovalDecisionRequest(
            approval_id=approval.id,
            payload_hash=approval.payload_hash,
        ),
        db,
    )
    after = calendar_api.calendar_overview(
        starts_from=None, starts_before=None, db=db
    )
    assert approved.status == "confirmed"
    assert approved.verified is True
    assert approved.provider_event_id == f"mailpilot{candidate.id.hex}"
    assert candidate.id in {item.id for item in after.events}
    assert after.candidates == []
    with pytest.raises(AppError) as duplicate:
        await calendar_api.approve_candidate(
            candidate.id,
            ApprovalDecisionRequest(
                approval_id=approval.id,
                payload_hash=approval.payload_hash,
            ),
            db,
        )
    assert duplicate.value.code == "CALENDAR_CANDIDATE_ALREADY_DECIDED"


def test_candidate_parameter_change_requires_new_approval(calendar_db) -> None:
    db, owner, _ = calendar_db
    candidate = CalendarDraft(
        user_id=owner.id,
        status="pending_approval",
        title="Original title",
        starts_at=datetime(2026, 10, 21, 2, 0, tzinfo=UTC),
        timezone="Asia/Singapore",
        source_evidence={"text": "Meet on 21 October at 10am"},
    )
    db.add(candidate)
    db.flush()
    original = new_calendar_approval(draft=candidate, user_id=owner.id)
    db.add(original)
    db.flush()

    updated = calendar_api.update_calendar_candidate(
        candidate.id,
        CalendarEventUpdate(title="Changed title"),
        db,
    )

    assert original.status == "superseded"
    assert updated.approval_id != original.id
    assert updated.approval_payload_hash != original.payload_hash


@pytest.mark.anyio
async def test_expired_approval_cannot_execute(calendar_db) -> None:
    db, owner, _ = calendar_db
    candidate = CalendarDraft(
        user_id=owner.id,
        status="pending_approval",
        title="Expired meeting",
        starts_at=datetime(2026, 10, 21, 2, 0, tzinfo=UTC),
        timezone="Asia/Singapore",
        source_evidence={"text": "Meet on 21 October at 10am"},
    )
    db.add(candidate)
    db.flush()
    approval = new_calendar_approval(draft=candidate, user_id=owner.id)
    approval.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.add(approval)
    db.flush()

    with pytest.raises(AppError) as expired:
        await calendar_api.approve_candidate(
            candidate.id,
            ApprovalDecisionRequest(
                approval_id=approval.id,
                payload_hash=approval.payload_hash,
            ),
            db,
        )

    assert expired.value.code == "APPROVAL_EXPIRED"
    assert approval.status == "expired"


def test_user_cannot_modify_another_users_event(calendar_db) -> None:
    db, _, stranger = calendar_db
    foreign = CalendarDraft(
        user_id=stranger.id,
        status="confirmed",
        title="Private event",
        starts_at=datetime(2026, 10, 22, 2, 0, tzinfo=UTC),
        timezone="Asia/Singapore",
        source_evidence={"source": "manual"},
    )
    db.add(foreign)
    db.flush()
    with pytest.raises(AppError) as error:
        calendar_api.update_event(
            foreign.id, CalendarEventUpdate(title="Unauthorized"), db
        )
    assert error.value.status_code == 404
