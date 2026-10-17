from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.skills.base import FailureStrategy
from app.skills.registry import SKILL_REGISTRY


EMAIL_INPUT = {
    "email_id": uuid4(),
    "subject": "Research study invitation",
    "sender": "research@example.com",
    "sent_at": datetime(2026, 10, 5, tzinfo=UTC),
    "body": "Register for the study on 7 October 2026 at 10:40.",
    "language": "en",
    "timezone": "Asia/Singapore",
}


VALID_OUTPUTS = {
    "TriageSkill": {
        "category": "event",
        "priority": "normal",
        "confidence": 0.9,
        "evidence": "Register for the study",
    },
    "SummarizeSkill": {
        "summary_zh": "邮件邀请收件人参加研究。",
        "summary_en": "The email invites the recipient to a research study.",
        "key_facts": ["7 October 2026", "10:40"],
    },
    "TranslateSkill": {
        "translated_text": "报名参加研究。",
        "source_language": "en",
        "target_language": "zh-CN",
        "preserved_html": True,
    },
    "ActionExtractionSkill": {
        "actions": [
            {
                "title": "Register",
                "evidence": "Register for the study",
                "confidence": 0.9,
            }
        ]
    },
    "ScheduleSkill": {
        "candidates": [
            {
                "title": "Research study",
                "start": "2026-10-07T10:40:00+08:00",
                "timezone": "Asia/Singapore",
                "evidence": "7 October 2026 at 10:40",
                "confidence": 0.9,
                "requires_approval": True,
            }
        ]
    },
    "ReplySkill": {
        "subject": "Re: Research study invitation",
        "body": "Thank you. I would like to participate.",
        "tone": "concise",
        "requires_approval": True,
    },
}


class FakeExecutor:
    def __init__(self, output: dict[str, object]) -> None:
        self.output = output
        self.calls = 0

    async def execute(self, **_: object) -> dict[str, object]:
        self.calls += 1
        return self.output


def skill_input(name: str) -> dict[str, object]:
    if name == "TranslateSkill":
        return {
            "text": "Register for the study.",
            "source_language": "en",
            "target_language": "zh-CN",
            "preserve_html": True,
        }
    if name == "ScheduleSkill":
        return {**EMAIL_INPUT, "reference_date": datetime(2026, 10, 5, tzinfo=UTC)}
    if name == "ReplySkill":
        return {**EMAIL_INPUT, "intent": "Accept the invitation", "tone": "concise"}
    return EMAIL_INPUT


@pytest.mark.anyio
@pytest.mark.parametrize("skill_name", sorted(SKILL_REGISTRY))
async def test_each_skill_runs_independently(skill_name: str) -> None:
    skill = SKILL_REGISTRY[skill_name]
    executor = FakeExecutor(VALID_OUTPUTS[skill_name])

    output = await skill.run(skill_input(skill_name), executor)

    assert output == skill.output_schema.model_validate(VALID_OUTPUTS[skill_name])
    assert executor.calls == 1
    assert skill.prompt_version


def test_registry_defines_tools_and_failure_strategy_for_every_skill() -> None:
    assert set(SKILL_REGISTRY) == {
        "TriageSkill",
        "SummarizeSkill",
        "TranslateSkill",
        "ActionExtractionSkill",
        "ScheduleSkill",
        "ReplySkill",
    }
    assert all(
        isinstance(skill.allowed_tools, tuple)
        and isinstance(skill.failure_strategy, FailureStrategy)
        for skill in SKILL_REGISTRY.values()
    )
    assert SKILL_REGISTRY["ScheduleSkill"].failure_strategy == FailureStrategy.RETURN_EMPTY
    assert SKILL_REGISTRY["ReplySkill"].failure_strategy == FailureStrategy.FAIL_CLOSED


@pytest.mark.anyio
async def test_skill_retries_invalid_structured_output_once() -> None:
    skill = SKILL_REGISTRY["TriageSkill"]

    class InvalidExecutor(FakeExecutor):
        async def execute(self, **_: object) -> dict[str, object]:
            self.calls += 1
            return {"category": "event", "priority": "urgent"}

    executor = InvalidExecutor({})
    with pytest.raises(Exception):
        await skill.run(EMAIL_INPUT, executor)

    assert executor.calls == skill.max_attempts


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("skill_name", "empty_field"),
    [("ActionExtractionSkill", "actions"), ("ScheduleSkill", "candidates")],
)
async def test_return_empty_failure_strategy(skill_name: str, empty_field: str) -> None:
    skill = SKILL_REGISTRY[skill_name]
    executor = FakeExecutor({empty_field: "not-a-list"})

    output = await skill.run(skill_input(skill_name), executor)

    assert getattr(output, empty_field) == []
    assert executor.calls == skill.max_attempts


@pytest.mark.anyio
async def test_translate_failure_returns_original_content() -> None:
    skill = SKILL_REGISTRY["TranslateSkill"]
    payload = skill_input("TranslateSkill")

    output = await skill.run(payload, FakeExecutor({"invalid": True}))

    assert output.translated_text == payload["text"]
    assert output.preserved_html is True

