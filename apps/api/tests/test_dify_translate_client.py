from __future__ import annotations

import asyncio

import httpx
import pytest

from app.core.config import Settings
from app.services.dify_client import DifyConfigurationError
from app.services.dify_translate_client import DifyTranslateClient


def test_mock_translation_uses_no_tokens_and_preserves_html_wrapper() -> None:
    response = asyncio.run(
        DifyTranslateClient(Settings(dify_mock_mode=True)).translate(
            email_id="11111111-1111-4111-8111-111111111111",
            source_language="en",
            target_language="zh-CN",
            content_type="html",
            content="<p>Hello</p>",
        )
    )

    assert response.data.total_tokens == 0
    assert response.data.outputs is not None
    assert "<p>Hello</p>" in response.data.outputs["translated_content"]


def test_real_translation_sends_only_declared_inputs() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer translate-secret"
            payload = __import__("json").loads(request.content)
            assert set(payload["inputs"]) == {
                "email_id",
                "source_language",
                "target_language",
                "content_type",
                "content",
            }
            return httpx.Response(
                200,
                json={
                    "workflow_run_id": "run-1",
                    "task_id": "task-1",
                    "data": {
                        "id": "run-1",
                        "workflow_id": "translate-workflow",
                        "status": "succeeded",
                        "outputs": {
                            "translated_content": "<p>你好</p>",
                            "email_id": payload["inputs"]["email_id"],
                        },
                        "total_tokens": 42,
                    },
                },
            )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as http_client:
            response = await DifyTranslateClient(
                Settings(
                    dify_mock_mode=False,
                    dify_translate_api_key="translate-secret",
                ),
                http_client=http_client,
            ).translate(
                email_id="11111111-1111-4111-8111-111111111111",
                source_language="en",
                target_language="zh-CN",
                content_type="html",
                content="<p>Hello</p>",
            )
        assert response.data.outputs == {
            "translated_content": "<p>你好</p>",
            "email_id": "11111111-1111-4111-8111-111111111111",
        }

    asyncio.run(run())


def test_real_translation_requires_separate_api_key() -> None:
    with pytest.raises(DifyConfigurationError, match="DIFY_TRANSLATE_API_KEY"):
        asyncio.run(
            DifyTranslateClient(
                Settings(dify_mock_mode=False, dify_translate_api_key="")
            ).translate(
                email_id="11111111-1111-4111-8111-111111111111",
                source_language="en",
                target_language="zh-CN",
                content_type="text",
                content="Hello",
            )
        )

