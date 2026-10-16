import json
from uuid import uuid4

import pytest

from app.api.analysis import _parse_dify_analysis
from app.core.errors import AppError


def test_parse_valid_dify_analysis() -> None:
    email_id = uuid4()
    result = _parse_dify_analysis(
        {
            "analysis": json.dumps(
                {
                    "email_id": str(email_id),
                    "category": "活动",
                    "summary": "A research study invitation.",
                    "translation_needed": True,
                    "actions": [{"title": "Register for a session"}],
                    "calendar_candidates": [
                        {
                            "title": "Research study",
                            "start": "2026-10-05T10:40:00+08:00",
                            "end": "2026-10-05T12:00:00+08:00",
                            "timezone": "Asia/Singapore",
                            "location": "ComLab 6",
                            "evidence": "Timeslot 1: 10:40 am - 12:00 pm",
                            "confidence": 0.98,
                        }
                    ],
                }
            )
        }
    )

    assert result.email_id == email_id
    assert result.category == "活动"
    assert result.calendar_candidates[0].confidence == 0.98


def test_rejects_missing_or_invalid_dify_analysis() -> None:
    with pytest.raises(AppError, match="required analysis"):
        _parse_dify_analysis({})

    with pytest.raises(AppError, match="failed validation"):
        _parse_dify_analysis({"analysis": '{"email_id":"not-a-uuid"}'})


def test_rejects_out_of_range_confidence() -> None:
    with pytest.raises(AppError, match="failed validation"):
        _parse_dify_analysis(
            {
                "analysis": {
                    "email_id": str(uuid4()),
                    "category": "活动",
                    "summary": "Summary",
                    "translation_needed": False,
                    "actions": [],
                    "calendar_candidates": [
                        {
                            "title": "Invalid candidate",
                            "start": "2026-10-05T10:40:00+08:00",
                            "timezone": "Asia/Singapore",
                            "evidence": "Source sentence",
                            "confidence": 1.5,
                        }
                    ],
                }
            }
        )
