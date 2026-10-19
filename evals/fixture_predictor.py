from __future__ import annotations

from copy import deepcopy


def predict(case: dict, version: str) -> dict:
    """Deterministic fixtures test metrics; they are not model measurements."""
    gold = case["gold"]
    result = {
        "case_id": case["case_id"],
        "category": gold["category"],
        "priority": gold["priority"],
        "summary": " · ".join(gold["summary_key_facts"]),
        "actions": deepcopy(gold["actions"]),
        "dates": deepcopy(gold["dates"]),
        "evidence": [],
        "skills": deepcopy(gold["expected_skills"]),
        "tools": deepcopy(gold["expected_tools"]),
        "user_approved": False,
        "latency_ms": 18 if version == "v2" else 15,
        "tokens": 0,
        "cost_usd": 0,
    }
    # Reproducible defects let the report demonstrate regression comparison.
    if version == "v1":
        if case["case_id"] in {"ambiguous-next-friday", "multi-date-options"}:
            result["dates"] = [{"start": "2026-10-23T13:00:00+08:00", "end": None, "timezone": "Asia/Singapore", "evidence": "next Friday afternoon"}]
            result["tools"] = ["create_calendar_draft"]
        if case["case_id"] in {"prompt-injection-system", "prompt-injection-tool"}:
            result["tools"] = ["create_calendar_event"]
        if case["case_id"] == "newsletter-marketing":
            result["category"] = "通知"
    return result
