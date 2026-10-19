from __future__ import annotations

import math
import re
from decimal import Decimal
from typing import Any

SENSITIVE = re.compile(r"(token|secret|password|api[_-]?key|authorization|cookie|oauth|refresh|access|body|html|raw|content)", re.I)


def redact(value: Any, key: str | None = None) -> Any:
    if key and SENSITIVE.search(key):
        return "[redacted]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value[:20]]
    if isinstance(value, (str, bytes)):
        text = value.decode(errors="replace") if isinstance(value, bytes) else value
        return text if len(text) <= 500 else text[:497] + "..."
    if isinstance(value, Decimal):
        return float(value)
    return value


def estimate_tokens(text: str | None) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def estimate_cost(model: str | None, input_tokens: int, output_tokens: int, settings: Any) -> Decimal:
    if not model:
        return Decimal("0")
    if "strong" in model.lower() or model == getattr(settings, "dify_strong_model", ""):
        input_price, output_price = settings.strong_model_input_cost_per_million, settings.strong_model_output_cost_per_million
    else:
        input_price, output_price = settings.fast_model_input_cost_per_million, settings.fast_model_output_cost_per_million
    return Decimal(str((input_tokens * input_price + output_tokens * output_price) / 1_000_000))
