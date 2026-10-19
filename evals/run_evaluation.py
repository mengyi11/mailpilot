#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fixture_predictor import predict as fixture_predict  # noqa: E402
from metrics import evaluate  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def parse_analysis(outputs: dict[str, Any]) -> dict[str, Any]:
    value = outputs.get("analysis", outputs)
    if isinstance(value, str):
        value = json.loads(value)
    actions = []
    for item in value.get("actions", []):
        copied = dict(item)
        evidence = copied.get("evidence")
        copied["evidence"] = evidence.get("text", "") if isinstance(evidence, dict) else evidence
        actions.append(copied)
    dates = []
    for item in value.get("extracted_dates", value.get("dates", [])):
        copied = dict(item)
        evidence = copied.get("evidence")
        copied["evidence"] = evidence.get("text", "") if isinstance(evidence, dict) else evidence
        dates.append(copied)
    evidence = [
        item.get("text", "") if isinstance(item, dict) else item
        for item in value.get("evidence", [])
    ]
    return {
        "category": value.get("category"),
        "priority": value.get("priority"),
        "summary": value.get("summary", ""),
        "actions": actions,
        "dates": dates,
        "evidence": evidence,
        "skills": value.get("selected_skills", value.get("skills", [])),
        "tools": value.get("selected_tools", value.get("tools", [])),
        "user_approved": False,
    }


async def live_prediction(client: Any, case: dict, version: str, key: str) -> dict:
    started = perf_counter()
    email = case["input"]
    payload = {
        "inputs": {
            "user_id": "mailpilot-benchmark",
            "email_id": case["case_id"],
            "subject": email["subject"],
            "sender": email["sender"],
            "sent_at": email["sent_at"],
            "body": f"<UNTRUSTED_EMAIL_CONTENT>\n{email['body']}\n</UNTRUSTED_EMAIL_CONTENT>",
            "language": email["language"],
            "timezone": email["timezone"],
            "prompt_version": version,
        },
        "response_mode": "blocking",
        "user": "mailpilot-benchmark",
    }
    try:
        response = await client.post(
            f"{os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1').rstrip('/')}/workflows/run",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        envelope = response.json()
        data = envelope["data"]
        prediction = parse_analysis(data.get("outputs") or {})
        prediction.update(
            case_id=case["case_id"],
            latency_ms=round((perf_counter() - started) * 1000, 2),
            tokens=int(data.get("total_tokens") or 0),
            cost_usd=float(data.get("total_price") or 0),
        )
        return prediction
    except Exception as exc:
        return {
            "case_id": case["case_id"],
            "error": type(exc).__name__,
            "latency_ms": round((perf_counter() - started) * 1000, 2),
            "tokens": 0,
            "cost_usd": 0,
        }


async def predictions(cases: list[dict], mode: str, version: str) -> list[dict]:
    if mode == "fixture":
        return [fixture_predict(case, version) for case in cases]
    key = os.getenv(f"DIFY_{version.upper()}_API_KEY", "")
    if not key:
        raise SystemExit(f"DIFY_{version.upper()}_API_KEY is required for live mode")
    import httpx

    async with httpx.AsyncClient(timeout=90) as client:
        # Sequential calls make provider rate limits and per-case latency easier
        # to interpret. The benchmark is only 20 cases.
        return [await live_prediction(client, case, version, key) for case in cases]


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def markdown_report(report: dict) -> str:
    v1, v2 = report["versions"]["v1"], report["versions"]["v2"]
    metrics = [
        ("Classification Macro F1", "classification_macro_f1", True),
        ("Action Item F1", "action_item_f1", True),
        ("Date Accuracy", "date_accuracy", True),
        ("Citation Accuracy", "citation_accuracy", True),
        ("Summary Fact Recall", "summary_fact_recall", True),
        ("Tool Selection Accuracy", "tool_selection_accuracy", True),
        ("Unsafe Action Rate", "unsafe_action_rate", True),
        ("Failure Rate", "failure_rate", True),
        ("Average Latency", "average_latency_ms", False),
        ("Average Tokens", "average_tokens", False),
        ("Estimated Cost USD", "estimated_cost_usd", False),
    ]
    lines = [
        "# MailPilot Prompt Evaluation Report",
        "",
        f"- Mode: **{report['mode']}**",
        f"- Generated: `{report['generated_at']}`",
        f"- Benchmark cases: **{report['case_count']}**",
    ]
    if report["mode"] == "fixture":
        lines += ["- ⚠️ Fixture mode validates the evaluator only; these are not real LLM quality scores."]
    lines += ["", "| Metric | Prompt V1 | Prompt V2 | Change |", "|---|---:|---:|---:|"]
    for label, key, as_percent in metrics:
        a, b = v1[key], v2[key]
        render = percent if as_percent else lambda value: f"{value:.4f}"
        lines.append(f"| {label} | {render(a)} | {render(b)} | {b-a:+.4f} |")
    lines += ["", "## Main failure types", ""]
    for version, result in (("V1", v1), ("V2", v2)):
        failures = result["failure_types"] or {"none": 0}
        lines.append(f"- **{version}:** " + ", ".join(f"{key}={value}" for key, value in failures.items()))
    lines += ["", "## Failed cases", ""]
    for version, result in (("V1", v1), ("V2", v2)):
        lines.append(f"### {version}")
        if not result["failed_cases"]:
            lines.append("No scoring failures.")
        else:
            lines.extend(f"- `{item['case_id']}`: {', '.join(item['reasons'])}" for item in result["failed_cases"])
        lines.append("")
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    parser.add_argument("--dataset", type=Path, default=ROOT / "benchmark.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "latest.json")
    args = parser.parse_args()
    cases = load_jsonl(args.dataset)
    if len(cases) != 20:
        raise SystemExit(f"Gold benchmark must contain exactly 20 cases, found {len(cases)}")
    v1_predictions = await predictions(cases, args.mode, "v1")
    v2_predictions = await predictions(cases, args.mode, "v2")
    report = {
        "mode": args.mode,
        "generated_at": datetime.now(ZoneInfo("Asia/Singapore")).isoformat(),
        "case_count": len(cases),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "prompt_labels": {
            "v1": os.getenv("DIFY_V1_LABEL", "prompt-v1"),
            "v2": os.getenv("DIFY_V2_LABEL", "prompt-v2"),
        },
        "versions": {
            "v1": evaluate(cases, v1_predictions),
            "v2": evaluate(cases, v2_predictions),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    markdown = args.output.with_suffix(".md")
    markdown.write_text(markdown_report(report) + "\n")
    print(f"Wrote {args.output}")
    print(f"Wrote {markdown}")


if __name__ == "__main__":
    asyncio.run(main())
