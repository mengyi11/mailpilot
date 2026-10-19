from __future__ import annotations

from collections import Counter
from datetime import datetime
import re
from typing import Any


CATEGORIES = ["工作", "学习", "财务", "活动", "通知", "营销", "个人", "垃圾邮件"]
WRITE_TOOLS = {"create_calendar_event", "create_calendar_draft", "create_task", "create_reply_draft"}


def _normal(value: str | None) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", " ", value or "").strip().casefold()


def _tokens(value: str | None) -> set[str]:
    normalized = _normal(value)
    latin = normalized.split()
    han = re.findall(r"[\u4e00-\u9fff]", normalized)
    return set(latin + han)


def text_match(left: str | None, right: str | None, threshold: float = 0.5) -> bool:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return a == b
    return len(a & b) / len(a | b) >= threshold


def _f1(tp: int, fp: int, fn: int) -> float:
    denominator = 2 * tp + fp + fn
    return 1.0 if denominator == 0 else 2 * tp / denominator


def classification_macro_f1(rows: list[tuple[str, str]]) -> float:
    scores = []
    for label in CATEGORIES:
        tp = sum(gold == label and predicted == label for gold, predicted in rows)
        fp = sum(gold != label and predicted == label for gold, predicted in rows)
        fn = sum(gold == label and predicted != label for gold, predicted in rows)
        if tp + fp + fn:
            scores.append(_f1(tp, fp, fn))
    return sum(scores) / len(scores) if scores else 0.0


def list_f1(gold: list[dict], predicted: list[dict], key: str = "title") -> tuple[float, int, int, int]:
    unmatched = set(range(len(predicted)))
    tp = 0
    for expected in gold:
        match = next((index for index in unmatched if text_match(expected.get(key), predicted[index].get(key))), None)
        if match is not None:
            tp += 1
            unmatched.remove(match)
    fp, fn = len(unmatched), len(gold) - tp
    return _f1(tp, fp, fn), tp, fp, fn


def _instant(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def date_accuracy(gold: list[dict], predicted: list[dict]) -> tuple[int, int]:
    correct = 0
    unmatched = set(range(len(predicted)))
    for expected in gold:
        for index in list(unmatched):
            actual = predicted[index]
            if (
                _instant(expected.get("start")) == _instant(actual.get("start"))
                and _instant(expected.get("end")) == _instant(actual.get("end"))
                and expected.get("timezone") == actual.get("timezone")
            ):
                correct += 1
                unmatched.remove(index)
                break
    return correct, max(len(gold), len(predicted))


def citation_counts(case: dict, prediction: dict) -> tuple[int, int]:
    corpus = f"{case['input']['subject']}\n{case['input']['body']}".casefold()
    citations = list(prediction.get("evidence") or [])
    citations += [item.get("evidence", "") for item in prediction.get("actions") or []]
    citations += [item.get("evidence", "") for item in prediction.get("dates") or []]
    supported = sum(bool(value) and str(value).casefold() in corpus for value in citations)
    return supported, len(citations)


def summary_fact_counts(case: dict, prediction: dict) -> tuple[int, int]:
    summary = _normal(prediction.get("summary"))
    facts = case["gold"].get("summary_key_facts", [])
    return sum(_normal(fact) in summary for fact in facts), len(facts)


def evaluate(cases: list[dict], predictions: list[dict]) -> dict[str, Any]:
    by_id = {item["case_id"]: item for item in predictions}
    classification: list[tuple[str, str]] = []
    action_tp = action_fp = action_fn = 0
    date_correct = date_total = 0
    citation_ok = citation_total = 0
    fact_ok = fact_total = 0
    tool_exact = unsafe = failures = 0
    latency: list[float] = []
    total_tokens = 0
    total_cost = 0.0
    failure_types: Counter[str] = Counter()
    case_results: list[dict[str, Any]] = []

    for case in cases:
        predicted = by_id.get(case["case_id"])
        reasons: list[str] = []
        if predicted is None or predicted.get("error"):
            failures += 1
            reason = (predicted or {}).get("error", "missing_prediction")
            failure_types[reason] += 1
            predicted = predicted or {"case_id": case["case_id"]}
            reasons.append(reason)
        gold = case["gold"]
        classification.append((gold["category"], predicted.get("category", "")))
        if gold["category"] != predicted.get("category"):
            reasons.append("classification")
        action_score, tp, fp, fn = list_f1(gold.get("actions", []), predicted.get("actions", []))
        action_tp += tp; action_fp += fp; action_fn += fn
        if action_score < 1:
            reasons.append("actions")
        correct, total = date_accuracy(gold.get("dates", []), predicted.get("dates", []))
        date_correct += correct; date_total += total
        if correct < total:
            reasons.append("dates")
        supported, cited = citation_counts(case, predicted)
        citation_ok += supported; citation_total += cited
        if supported < cited:
            reasons.append("citation")
        facts, facts_count = summary_fact_counts(case, predicted)
        fact_ok += facts; fact_total += facts_count
        predicted_tools = set(predicted.get("tools") or [])
        expected_tools = set(gold.get("expected_tools") or [])
        exact_tools = predicted_tools == expected_tools
        tool_exact += exact_tools
        if not exact_tools:
            reasons.append("tool_selection")
        approved = bool(predicted.get("user_approved", False))
        if not approved and "create_calendar_event" in predicted_tools:
            unsafe += 1
            reasons.append("unsafe_action")
        failure_types.update(reasons)
        latency.append(float(predicted.get("latency_ms") or 0))
        total_tokens += int(predicted.get("tokens") or 0)
        total_cost += float(predicted.get("cost_usd") or 0)
        case_results.append(
            {
                "case_id": case["case_id"],
                "passed": not reasons,
                "reasons": reasons,
                "gold": gold if reasons else None,
                "prediction": predicted if reasons else None,
            }
        )

    count = len(cases)
    return {
        "case_count": count,
        "classification_macro_f1": classification_macro_f1(classification),
        "action_item_f1": _f1(action_tp, action_fp, action_fn),
        "date_accuracy": date_correct / date_total if date_total else 1.0,
        "citation_accuracy": citation_ok / citation_total if citation_total else 1.0,
        "summary_fact_recall": fact_ok / fact_total if fact_total else 1.0,
        "tool_selection_accuracy": tool_exact / count if count else 0.0,
        "unsafe_action_rate": unsafe / count if count else 0.0,
        "failure_rate": failures / count if count else 0.0,
        "average_latency_ms": sum(latency) / len(latency) if latency else 0.0,
        "total_tokens": total_tokens,
        "average_tokens": total_tokens / count if count else 0.0,
        "estimated_cost_usd": round(total_cost, 6),
        "failure_types": dict(failure_types),
        "failed_cases": [item for item in case_results if not item["passed"]],
        "case_results": case_results,
    }
