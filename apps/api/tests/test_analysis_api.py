import json
from uuid import uuid4

import pytest

from app.api.analysis import (
    _parse_dify_analysis,
    _split_bilingual_summary,
    _validate_or_repair_analysis,
)
from app.core.errors import AppError
from app.services.dify_client import DifyConfigurationError


def standard_payload(email_id):
    return {
        "email_id": str(email_id),
        "category": "活动",
        "priority": "high",
        "summary": "A research study invitation.",
        "translation_needed": True,
        "evidence": [],
        "actions": [{
            "title": "Register for a session", "description": None, "due_at": None,
            "evidence": {"text": "Please register", "source": "email_body", "confidence": 0.9},
            "confidence": 0.9,
        }],
        "extracted_dates": [{
            "title": "Research study", "start": "2026-10-05T10:40:00+08:00",
            "end": "2026-10-05T12:00:00+08:00", "timezone": "Asia/Singapore",
            "location": "ComLab 6", "description": None,
            "evidence": {"text": "Timeslot 1", "source": "email_body", "confidence": 0.98},
            "confidence": 0.98,
        }],
    }


class UnavailableRepairClient:
    async def repair(self, **_kwargs):
        raise DifyConfigurationError("not configured")


class SuccessfulRepairClient:
    def __init__(self, payload):
        self.payload = payload

    async def repair(self, **_kwargs):
        return self.payload


def test_parse_valid_standard_dify_analysis() -> None:
    email_id = uuid4()
    result = _parse_dify_analysis({"analysis": json.dumps(standard_payload(email_id))})
    assert result.email_id == email_id
    assert result.category == "活动"
    assert result.priority == "high"
    assert result.extracted_dates[0].confidence == 0.98


def test_rejects_missing_or_invalid_dify_analysis() -> None:
    with pytest.raises(AppError, match="required analysis"):
        _parse_dify_analysis({})
    with pytest.raises(AppError, match="failed validation"):
        _parse_dify_analysis({"analysis": '{"email_id":"not-a-uuid"}'})


def test_rejects_naive_date_invalid_timezone_and_confidence() -> None:
    payload = standard_payload(uuid4())
    payload["extracted_dates"][0].update(start="2026-10-05T10:40:00", timezone="Singapore", confidence=1.5)
    with pytest.raises(AppError, match="failed validation"):
        _parse_dify_analysis({"analysis": payload})


@pytest.mark.anyio
async def test_deterministic_repair_converts_legacy_shape() -> None:
    email_id = uuid4()
    legacy = {
        "email_id": str(email_id), "category": "event", "summary": "Legacy output",
        "translation_needed": False, "actions": [],
        "calendar_candidates": [
            {"title": "Valid", "start": "2026-10-05T10:40:00+08:00", "timezone": "Asia/Singapore", "evidence": "Source", "confidence": 0.8},
            {"title": "Unsafe", "start": "2026-10-05T10:40:00", "timezone": "Not/AZone", "evidence": "Bad", "confidence": 5},
        ],
    }
    result, mode, read_only = await _validate_or_repair_analysis(
        {"analysis": legacy}, expected_email_id=email_id, repair_client=UnavailableRepairClient()
    )
    assert (mode, read_only, result.priority) == ("schema_repair", False, "normal")
    assert len(result.extracted_dates) == 1


@pytest.mark.anyio
async def test_strong_model_is_used_after_local_repair_fails() -> None:
    email_id = uuid4()
    result, mode, read_only = await _validate_or_repair_analysis(
        {"analysis": {"email_id": str(email_id)}}, expected_email_id=email_id,
        repair_client=SuccessfulRepairClient(standard_payload(email_id)),
    )
    assert (mode, read_only) == ("strong_model_repair", False)
    assert result.summary == "A research study invitation."


@pytest.mark.anyio
async def test_unrepairable_output_becomes_safe_read_only() -> None:
    email_id = uuid4()
    result, mode, read_only = await _validate_or_repair_analysis(
        {"analysis": {"email_id": str(email_id)}}, expected_email_id=email_id,
        repair_client=UnavailableRepairClient(),
    )
    assert (mode, read_only) == ("read_only_fallback", True)
    assert result.actions == [] and result.extracted_dates == []


@pytest.mark.anyio
async def test_mismatched_email_id_cannot_create_calendar_data() -> None:
    expected = uuid4()
    result, mode, read_only = await _validate_or_repair_analysis(
        {"analysis": standard_payload(uuid4())}, expected_email_id=expected,
        repair_client=UnavailableRepairClient(),
    )
    assert (mode, read_only, result.email_id) == ("read_only_fallback", True, expected)
    assert result.extracted_dates == []


def test_splits_bilingual_summary_with_optional_blank_line() -> None:
    display, english, chinese = _split_bilingual_summary(
        "ZH: 中文摘要。\n\nEN: English summary."
    )

    assert display == "English summary."
    assert english == "English summary."
    assert chinese == "中文摘要。"


def test_keeps_legacy_single_language_summary() -> None:
    display, english, chinese = _split_bilingual_summary("Legacy English summary.")

    assert display == "Legacy English summary."
    assert english == "Legacy English summary."
    assert chinese is None
