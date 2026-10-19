from __future__ import annotations

from datetime import UTC, datetime
from contextlib import nullcontext
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.api.tools import verify_dify_tool_key
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models.agent import AgentRun, ToolCall
from app.db.models.email import Email, EmailThread
from app.db.models.identity import EmailAccount, User
from app.db.session import SessionLocal
from app.tools.base import BaseTool, ToolContext, ToolExecutionError
from app.tools.implementations import TOOLS
from app.tools.registry import TOOL_REGISTRY, ToolRegistry
from app.main import app


ALL_PERMISSIONS = frozenset(
    {"email:read", "preferences:read", "task:write", "draft:write"}
)


@pytest.fixture
def tool_data():
    db = SessionLocal()
    owner = User(email=f"owner-{uuid4()}@example.com", display_name="Owner")
    stranger = User(email=f"stranger-{uuid4()}@example.com", display_name="Stranger")
    db.add_all([owner, stranger])
    db.flush()
    account = EmailAccount(
        user_id=owner.id,
        provider="test",
        provider_account_id=str(uuid4()),
        email_address=owner.email,
        sync_status="connected",
    )
    db.add(account)
    db.flush()
    thread = EmailThread(
        email_account_id=account.id,
        provider_thread_id=str(uuid4()),
        subject="Project launch",
        message_count=1,
    )
    db.add(thread)
    db.flush()
    email = Email(
        email_account_id=account.id,
        thread_id=thread.id,
        provider_message_id=str(uuid4()),
        sender={"name": "Alex", "email": "alex@example.com"},
        recipients={"to": [{"name": "Owner", "email": owner.email}], "cc": []},
        subject="Project launch decision",
        snippet="The customer selected option A.",
        body_text="The customer selected option A.",
        cleaned_text="The customer selected option A.",
        received_at=datetime.now(UTC),
        labels=["INBOX"],
    )
    db.add(email)
    db.flush()
    yield db, owner, stranger, thread, email
    db.rollback()
    db.close()


def tool(name: str):
    return next(item for item in TOOLS if item.name == name)


def context(user_id, permissions=ALL_PERMISSIONS):
    return ToolContext(user_id=user_id, permissions=permissions, trace_id=uuid4().hex)


def test_registry_exposes_all_required_tools() -> None:
    assert {item["name"] for item in TOOL_REGISTRY.definitions()} == {
        "get_email",
        "get_email_thread",
        "search_emails",
        "retrieve_related_emails",
        "get_user_preferences",
        "create_task",
        "create_reply_draft",
        "check_calendar_availability",
        "create_calendar_draft",
        "create_calendar_event",
        "get_calendar_event",
    }
    assert all(item["input_schema"] for item in TOOL_REGISTRY.definitions())


def test_openapi_exposes_each_tool_and_endpoint_defaults_to_deny() -> None:
    paths = app.openapi()["paths"]
    for name in {item["name"] for item in TOOL_REGISTRY.definitions()}:
        assert paths[f"/tools/{name}"]["post"]["operationId"] == name
    with pytest.raises(AppError) as error:
        verify_dify_tool_key(None, get_settings())
    assert error.value.status_code == 401


@pytest.mark.anyio
async def test_get_email_and_cross_user_isolation(tool_data) -> None:
    db, owner, stranger, _, email = tool_data
    result = await tool("get_email").execute(
        db, context(owner.id), tool("get_email").parse_input({"email_id": email.id})
    )
    assert result["id"] == str(email.id)
    with pytest.raises(ToolExecutionError, match="not found"):
        await tool("get_email").execute(
            db,
            context(stranger.id),
            tool("get_email").parse_input({"email_id": email.id}),
        )


@pytest.mark.anyio
async def test_get_thread_and_search_email(tool_data) -> None:
    db, owner, _, thread, email = tool_data
    thread_result = await tool("get_email_thread").execute(
        db,
        context(owner.id),
        tool("get_email_thread").parse_input({"thread_id": thread.id}),
    )
    search_result = await tool("search_emails").execute(
        db,
        context(owner.id),
        tool("search_emails").parse_input({"query": "option A"}),
    )
    assert thread_result["messages"][0]["id"] == str(email.id)
    assert search_result["count"] == 1


@pytest.mark.anyio
async def test_retrieve_related_emails_uses_owned_rag(monkeypatch, tool_data) -> None:
    db, owner, _, _, email = tool_data

    async def fake_search(*_args, **_kwargs):
        return SimpleNamespace(
            model_dump=lambda **_: {
                "citations": [{"email_id": str(email.id)}],
                "no_results": False,
            }
        )

    monkeypatch.setattr("app.tools.implementations.RagService.search", fake_search)
    result = await tool("retrieve_related_emails").execute(
        db,
        context(owner.id),
        tool("retrieve_related_emails").parse_input(
            {"email_id": email.id, "query": "customer decision", "top_k": 3}
        ),
    )
    assert result["citations"][0]["email_id"] == str(email.id)


@pytest.mark.anyio
async def test_preferences_task_and_reply_draft_tools(tool_data) -> None:
    db, owner, _, _, email = tool_data
    preferences = await tool("get_user_preferences").execute(
        db, context(owner.id), tool("get_user_preferences").parse_input({})
    )
    task = await tool("create_task").execute(
        db,
        context(owner.id),
        tool("create_task").parse_input(
            {"email_id": email.id, "title": "Follow up", "priority": "high"}
        ),
    )
    draft = await tool("create_reply_draft").execute(
        db,
        context(owner.id),
        tool("create_reply_draft").parse_input(
            {"email_id": email.id, "subject": "Re: Project", "body": "Thank you."}
        ),
    )
    assert preferences["must_not_use_as_email_fact"] is True
    assert task["status"] == "open"
    assert draft["requires_approval"] is True


def test_tool_permission_is_checked_before_execution() -> None:
    with pytest.raises(ToolExecutionError, match="Permission"):
        tool("create_task").authorize(context(uuid4(), frozenset({"email:read"})))


class FakeInput(BaseModel):
    value: str


class FakeWriteTool(BaseTool[FakeInput]):
    name = "fake_write"
    description = "Test idempotent writes."
    permission = "fake:write"
    input_model = FakeInput

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, db, context, arguments):
        self.calls += 1
        return {"value": arguments.value, "created": self.calls}


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def one_or_none(self):
        return self.value


class FakeDb:
    def __init__(self) -> None:
        self.run = None
        self.call = None
        self.cached = None

    def execute(self, _statement):
        return FakeScalarResult(self.cached)

    def add(self, value):
        if isinstance(value, AgentRun):
            self.run = value
        if isinstance(value, ToolCall):
            self.call = value

    def flush(self):
        if self.run is not None and self.run.id is None:
            self.run.id = uuid4()
        if self.call is not None and self.call.id is None:
            self.call.id = uuid4()

    def commit(self):
        if self.call is not None and self.call.status == "completed":
            self.cached = (self.call, self.run)

    def begin_nested(self):
        return nullcontext()


@pytest.mark.anyio
async def test_registry_reuses_successful_idempotent_result() -> None:
    fake_tool = FakeWriteTool()
    registry = ToolRegistry([fake_tool])
    db = FakeDb()
    user_id = uuid4()
    arguments = {"value": "one write"}

    first = await registry.execute(
        db,
        name="fake_write",
        user_id=user_id,
        arguments=arguments,
        permissions=frozenset({"fake:write"}),
        idempotency_key="same-request-key",
        trace_id=None,
        timeout_seconds=1,
    )
    second = await registry.execute(
        db,
        name="fake_write",
        user_id=user_id,
        arguments=arguments,
        permissions=frozenset({"fake:write"}),
        idempotency_key="same-request-key",
        trace_id=None,
        timeout_seconds=1,
    )

    assert first.ok is True and first.cached is False
    assert second.ok is True and second.cached is True
    assert first.data == second.data
    assert fake_tool.calls == 1
