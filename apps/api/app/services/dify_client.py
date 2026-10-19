from __future__ import annotations

import json
import asyncio
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
        if self.settings.dify_mock_mode:
            return self._mock_workflow_response(email)

        if not self.settings.dify_api_key:
            raise DifyConfigurationError(
                "DIFY_API_KEY is missing; publish the Dify workflow and add its key to apps/api/.env"
            )

        inputs = email.to_workflow_inputs()
        max_chars = max(self.settings.dify_max_input_chars, 1000)
        if len(inputs["body"]) > max_chars:
            head_length = int(max_chars * 0.75)
            tail_length = max_chars - head_length
            inputs["body"] = (
                inputs["body"][:head_length]
                + "\n\n[中间内容因 Token 成本限制已省略]\n\n"
                + inputs["body"][-tail_length:]
            )

        payload = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": email.user_id,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_api_key}",
            "Content-Type": "application/json",
        }

        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=60.0)
        response = None
        last_error: Exception | None = None
        try:
            for attempt in range(max(1, self.settings.dify_max_retries)):
                try:
                    response = await client.post(
                        f"{self.settings.dify_base_url.rstrip('/')}/workflows/run",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code not in {429, 500, 502, 503, 504}:
                        break
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_error = exc
                if attempt + 1 < max(1, self.settings.dify_max_retries):
                    await asyncio.sleep(0.25 * (2**attempt))
        finally:
            if owns_client:
                await client.aclose()

        if response is None:
            raise DifyAPIError("Dify workflow timed out or could not be reached") from last_error

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

    @staticmethod
    def _mock_workflow_response(email: DifyEmailInput) -> DifyWorkflowResponse:
        """Return deterministic UI-test data without sending anything to Dify."""
        analysis = {
            "email_id": email.email_id,
            "category": "通知",
            "priority": "normal",
            "summary": (
                f"ZH: 这是“{email.subject}”的本地模拟分析结果。本次请求没有调用 Dify 或大模型，因此不会消耗 Token。\n"
                f"EN: This is a local mock analysis of “{email.subject}”. No Dify or LLM request was made, so it used zero tokens."
            ),
            "translation_needed": email.language not in {"zh", "zh-CN", "zh-TW"},
            "evidence": [],
            "actions": [],
            "extracted_dates": [
                {
                    "title": "模拟日历候选",
                    "start": email.sent_at.isoformat(),
                    "end": None,
                    "timezone": email.timezone,
                    "location": "MailPilot 测试环境",
                    "description": "仅用于测试前端排版，不代表邮件真实内容。",
                    "evidence": {
                        "text": "DIFY_MOCK_MODE=true 生成的模拟候选",
                        "source": "email_body",
                        "confidence": 0.95,
                    },
                    "confidence": 0.95,
                }
            ],
        }
        return DifyWorkflowResponse(
            workflow_run_id=f"mock-{email.email_id}",
            task_id=f"mock-task-{email.email_id}",
            data=DifyWorkflowData(
                id=f"mock-{email.email_id}",
                workflow_id="local-mock-workflow",
                status="succeeded",
                outputs={"analysis": json.dumps(analysis, ensure_ascii=False)},
                elapsed_time=0.0,
                total_tokens=0,
                total_steps=0,
            ),
        )
