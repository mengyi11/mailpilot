from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, get_settings


class DifyConfigurationError(RuntimeError):
    """Raised when the backend is not configured to call Dify."""


class DifyAPIError(RuntimeError):
    """Raised when Dify rejects a workflow request or returns invalid data."""


class DifyEmailInput(BaseModel):
    """The only email data that MailPilot sends to the Dify workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(min_length=1)
    email_id: str = Field(min_length=1)
    subject: str
    sender: str
    sent_at: datetime
    body: str = Field(min_length=1, description="Cleaned email text, never raw OAuth data")
    language: str = Field(min_length=2)
    timezone: str = Field(min_length=1)

    def to_workflow_inputs(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "email_id": self.email_id,
            "subject": self.subject,
            "sender": self.sender,
            "sent_at": self.sent_at.isoformat(),
            "body": self.body,
            "language": self.language,
            "timezone": self.timezone,
        }


class DifyWorkflowData(BaseModel):
    id: str
    workflow_id: str
    status: str
    outputs: dict[str, Any] | None = None
    error: str | None = None
    elapsed_time: float | None = None
    total_tokens: int | None = None
    total_steps: int | None = None


class DifyWorkflowResponse(BaseModel):
    workflow_run_id: str
    task_id: str
    data: DifyWorkflowData


class DifyClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http_client = http_client

    async def run_email_workflow(
        self,
        email: DifyEmailInput,
        *,
        response_mode: Literal["blocking", "streaming"] = "blocking",
    ) -> DifyWorkflowResponse:
        if not self.settings.dify_api_key:
            raise DifyConfigurationError(
                "DIFY_API_KEY is missing; publish the Dify workflow and add its key to apps/api/.env"
            )

        payload = {
            "inputs": email.to_workflow_inputs(),
            "response_mode": response_mode,
            "user": email.user_id,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_api_key}",
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
        except httpx.TimeoutException as exc:
            raise DifyAPIError("Dify workflow timed out") from exc
        except httpx.HTTPError as exc:
            raise DifyAPIError("Could not reach Dify") from exc
        finally:
            if owns_client:
                await client.aclose()

        if response.is_error:
            request_id = response.headers.get("x-request-id", "unknown")
            raise DifyAPIError(
                f"Dify returned HTTP {response.status_code} (request_id={request_id})"
            )

        try:
            result = DifyWorkflowResponse.model_validate(response.json())
        except (ValueError, TypeError) as exc:
            raise DifyAPIError("Dify returned an invalid workflow response") from exc

        if result.data.status != "succeeded":
            raise DifyAPIError(result.data.error or f"Dify workflow ended with {result.data.status}")
        return result
