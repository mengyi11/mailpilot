from __future__ import annotations

from typing import Literal

import httpx

from app.core.config import Settings, get_settings
from app.services.dify_client import (
    DifyAPIError,
    DifyConfigurationError,
    DifyWorkflowResponse,
)


class DifyTranslateClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http_client = http_client

    async def translate(
        self,
        *,
        email_id: str,
        source_language: str,
        target_language: str,
        content_type: Literal["html", "text"],
        content: str,
    ) -> DifyWorkflowResponse:
        if self.settings.dify_mock_mode:
            return self._mock_response(
                email_id=email_id,
                source_language=source_language,
                target_language=target_language,
                content_type=content_type,
                content=content,
            )
        if not self.settings.dify_translate_api_key:
            raise DifyConfigurationError(
                "DIFY_TRANSLATE_API_KEY is missing from the API server"
            )

        payload = {
            "inputs": {
                "email_id": email_id,
                "source_language": source_language,
                "target_language": target_language,
                "content_type": content_type,
                "content": content[:12000],
            },
            "response_mode": "blocking",
            "user": email_id,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.dify_translate_api_key}",
            "Content-Type": "application/json",
        }
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=90.0)
        try:
            response = await client.post(
                f"{self.settings.dify_base_url.rstrip('/')}/workflows/run",
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise DifyAPIError("TranslateSkill timed out") from exc
        except httpx.HTTPError as exc:
            raise DifyAPIError("Could not reach TranslateSkill") from exc
        finally:
            if owns_client:
                await client.aclose()

        if response.is_error:
            request_id = response.headers.get("x-request-id", "unknown")
            raise DifyAPIError(
                f"TranslateSkill returned HTTP {response.status_code} "
                f"(request_id={request_id})"
            )
        try:
            result = DifyWorkflowResponse.model_validate(response.json())
        except (TypeError, ValueError) as exc:
            raise DifyAPIError("TranslateSkill returned an invalid response") from exc
        if result.data.status != "succeeded":
            raise DifyAPIError(
                result.data.error or f"TranslateSkill ended with {result.data.status}"
            )
        return result

    @staticmethod
    def _mock_response(
        *,
        email_id: str,
        source_language: str,
        target_language: str,
        content_type: str,
        content: str,
    ) -> DifyWorkflowResponse:
        translated = (
            f'<div data-mailpilot-mock="true">[模拟译文] {content}</div>'
            if content_type == "html"
            else f"[模拟译文] {content}"
        )
        return DifyWorkflowResponse.model_validate(
            {
                "workflow_run_id": f"mock-translate-{email_id}",
                "task_id": f"mock-translate-task-{email_id}",
                "data": {
                    "id": f"mock-translate-{email_id}",
                    "workflow_id": "local-mock-translate-skill",
                    "status": "succeeded",
                    "outputs": {
                        "translated_content": translated,
                        "email_id": email_id,
                        "source_language": source_language,
                        "target_language": target_language,
                        "content_type": content_type,
                    },
                    "elapsed_time": 0,
                    "total_tokens": 0,
                    "total_steps": 0,
                },
            }
        )

