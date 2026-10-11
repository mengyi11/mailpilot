import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.services.dify_client import (
    DifyClient,
    DifyConfigurationError,
    DifyEmailInput,
)


def sample_email() -> DifyEmailInput:
    return DifyEmailInput(
        user_id="user-1",
        email_id="email-1",
        subject="Research study invitation",
        sender="research@example.com",
        sent_at=datetime(2026, 10, 5, 10, 40, tzinfo=UTC),
        body="Choose one of the available study sessions.",
        language="en",
        timezone="Asia/Singapore",
    )


def test_client_sends_backend_key_and_workflow_inputs() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.dify.ai/v1/workflows/run"
        assert request.headers["Authorization"] == "Bearer test-secret"
        payload = __import__("json").loads(request.content)
        assert payload["user"] == "user-1"
        assert payload["inputs"]["email_id"] == "email-1"
        assert payload["inputs"]["timezone"] == "Asia/Singapore"
        assert payload["inputs"]["sent_at"] == "2026-10-05T10:40:00+00:00"
        return httpx.Response(
            200,
            json={
                "workflow_run_id": "run-1",
                "task_id": "task-1",
                "data": {
                    "id": "run-1",
                    "workflow_id": "workflow-1",
                    "status": "succeeded",
                    "outputs": {"email_id": "email-1"},
                },
            },
        )

    async def run() -> object:
        settings = Settings(dify_api_key="test-secret")
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            return await DifyClient(
                settings, http_client=http_client
            ).run_email_workflow(sample_email())

    result = asyncio.run(run())

    assert result.data.outputs == {"email_id": "email-1"}


def test_client_requires_api_key() -> None:
    async def run() -> None:
        await DifyClient(Settings(dify_api_key="")).run_email_workflow(sample_email())

    with pytest.raises(DifyConfigurationError, match="DIFY_API_KEY"):
        asyncio.run(run())
