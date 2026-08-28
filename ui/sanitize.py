from __future__ import annotations

import json
from typing import Any


_SENSITIVE_KEYS = {
    "message",
    "content",
    "value",
    "password",
    "passphrase",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "session",
}

_NOISY_KEYS = {
    "sources",
    "steps",
}


def _redacted(value: Any) -> str:
    length = len(str(value))
    return f"[REDACTED · {length} chars]"


def _compact(value: Any, *, depth: int = 0) -> Any:
    if depth >= 3:
        return "[…]"

    if isinstance(value, dict):
        compact: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).casefold()

            if lowered in _SENSITIVE_KEYS:
                compact[str(key)] = _redacted(item)
                continue

            if lowered == "sources" and isinstance(item, list):
                compact["sources"] = [
                    {
                        "rank": source.get("rank"),
                        "title": source.get("title"),
                        "fetch_ok": source.get("fetch_ok"),
                    }
                    for source in item[:5]
                    if isinstance(source, dict)
                ]
                continue

            if lowered == "steps" and isinstance(item, list):
                compact["steps"] = f"{len(item)} automation steps"
                continue

            compact[str(key)] = _compact(
                item,
                depth=depth + 1,
            )
        return compact

    if isinstance(value, (list, tuple)):
        items = [
            _compact(item, depth=depth + 1)
            for item in value[:8]
        ]
        if len(value) > 8:
            items.append(f"[… +{len(value) - 8} more]")
        return items

    text = str(value)
    if len(text) > 240:
        return text[:237] + "…"
    return value


def tool_payload_for_log(
    tool_name: str,
    payload: Any,
    *,
    max_chars: int = 850,
) -> str:
    compact = _compact(payload)
    rendered = json.dumps(
        compact,
        ensure_ascii=False,
        separators=(", ", ": "),
        default=str,
    )

    prefix = f"{tool_name}: "
    budget = max(120, int(max_chars)) - len(prefix)

    if len(rendered) > budget:
        rendered = rendered[: max(0, budget - 1)] + "…"

    return prefix + rendered


def clean_log_line(text: Any, *, max_chars: int = 900) -> str:
    clean = " ".join(str(text).split())
    limit = max(120, int(max_chars))
    if len(clean) > limit:
        return clean[: limit - 1] + "…"
    return clean
