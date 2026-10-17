from __future__ import annotations

from app.skills.base import FailureStrategy, SkillDefinition
from app.skills.contracts import (
    ActionExtractionOutput,
    EmailSkillInput,
    ReplyInput,
    ReplyOutput,
    ScheduleInput,
    ScheduleOutput,
    SummarizeOutput,
    TranslateInput,
    TranslateOutput,
    TriageOutput,
)


TRIAGE_SKILL = SkillDefinition(
    name="TriageSkill",
    prompt_version="triage-v1",
    description="Classify an email and estimate urgency from explicit evidence.",
    prompt="Classify the email. Return only schema fields and never infer missing urgency.",
    input_schema=EmailSkillInput,
    output_schema=TriageOutput,
    allowed_tools=(),
    failure_strategy=FailureStrategy.FAIL_CLOSED,
)

SUMMARIZE_SKILL = SkillDefinition(
    name="SummarizeSkill",
    prompt_version="summarize-v2-bilingual",
    description="Create concise Chinese and English summaries while retaining key facts.",
    prompt=(
        "Summarize only supported facts. Preserve people, dates, time, place, money, and URLs. "
        "Return concise summary_zh, summary_en, and key_facts."
    ),
    input_schema=EmailSkillInput,
    output_schema=SummarizeOutput,
    allowed_tools=(),
    failure_strategy=FailureStrategy.FAIL_CLOSED,
)

TRANSLATE_SKILL = SkillDefinition(
    name="TranslateSkill",
    prompt_version="translate-v1",
    description="Translate EN/ZH email content without changing its HTML structure.",
    prompt=(
        "Translate faithfully. Preserve HTML tags, links, names, numbers, and formatting; "
        "do not add explanations."
    ),
    input_schema=TranslateInput,
    output_schema=TranslateOutput,
    allowed_tools=("ocr_attachment_text",),
    failure_strategy=FailureStrategy.USE_ORIGINAL,
    fallback_factory=lambda value: {
        "translated_text": value.text,
        "source_language": value.source_language,
        "target_language": value.target_language,
        "preserved_html": value.preserve_html,
    },
)

ACTION_EXTRACTION_SKILL = SkillDefinition(
    name="ActionExtractionSkill",
    prompt_version="action-extraction-v1",
    description="Extract explicit tasks, deadlines, and their source evidence.",
    prompt="Extract only explicit actions. Every action must quote evidence and include confidence.",
    input_schema=EmailSkillInput,
    output_schema=ActionExtractionOutput,
    allowed_tools=(),
    failure_strategy=FailureStrategy.RETURN_EMPTY,
    fallback_factory=lambda _: {"actions": []},
)

SCHEDULE_SKILL = SkillDefinition(
    name="ScheduleSkill",
    prompt_version="schedule-v1",
    description="Convert explicit date/time facts into calendar drafts for human approval.",
    prompt=(
        "Resolve dates using reference_date and timezone. Never write to a calendar. "
        "Return evidence-backed candidates with requires_approval=true."
    ),
    input_schema=ScheduleInput,
    output_schema=ScheduleOutput,
    allowed_tools=("timezone_lookup",),
    failure_strategy=FailureStrategy.RETURN_EMPTY,
    fallback_factory=lambda _: {"candidates": []},
)

REPLY_SKILL = SkillDefinition(
    name="ReplySkill",
    prompt_version="reply-v1",
    description="Draft a reply in the requested tone without sending it.",
    prompt=(
        "Draft a reply from the supplied email and intent. Do not invent commitments and never send. "
        "Return requires_approval=true."
    ),
    input_schema=ReplyInput,
    output_schema=ReplyOutput,
    allowed_tools=("user_preferences_read",),
    failure_strategy=FailureStrategy.FAIL_CLOSED,
)

SKILL_REGISTRY = {
    skill.name: skill
    for skill in (
        TRIAGE_SKILL,
        SUMMARIZE_SKILL,
        TRANSLATE_SKILL,
        ACTION_EXTRACTION_SKILL,
        SCHEDULE_SKILL,
        REPLY_SKILL,
    )
}

