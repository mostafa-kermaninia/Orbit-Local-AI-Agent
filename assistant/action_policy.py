from __future__ import annotations

import re
from typing import Any


def explicit_user_authorization(
    tool_name: str,
    user_text: str,
    arguments: dict[str, Any],
) -> bool:
    """Deterministic guard for the current side-effecting tools.

    Retrieved tool/web content cannot create authorization. The original latest
    user message must itself contain a recognizable action request.

    This is intentionally conservative; the normal LLM/tool layer still handles
    the flexible natural-language interpretation for read-only tools.
    """
    text = " ".join(str(user_text).casefold().split())

    if tool_name == "send_telegram_message":
        contact = " ".join(
            str(arguments.get("contact", "")).casefold().split()
        )
        contact_named = bool(contact and contact in text)
        telegram_named = bool(
            re.search(r"\btelegram\b", text)
            or "تلگرام" in text
        )

        # Strong English action verbs. "message" alone is not enough unless the
        # selected contact is also explicitly named, avoiding phrases such as
        # "research Telegram message security".
        send_requested = bool(
            re.search(r"\b(send|text|dm)\b", text)
        )
        message_contact_requested = bool(
            contact_named
            and re.search(r"\bmessage\b", text)
        )

        # Strong Persian imperative forms.
        persian_requested = any(
            phrase in text
            for phrase in (
                "بفرست",
                "ارسال کن",
                "پیام بده",
                "پیام بفرست",
            )
        )

        return (
            (send_requested and (contact_named or telegram_named))
            or message_contact_requested
            or (persian_requested and (contact_named or telegram_named))
        )

    if tool_name == "open_app":
        app = " ".join(
            str(arguments.get("app", "")).casefold().split()
        )
        if not app or app not in text:
            return False

        english_command = bool(
            re.search(
                r"(?:^|\bthen\s+|\band\s+then\s+)"
                r"(?:please\s+|can\s+you\s+|could\s+you\s+|would\s+you\s+)?"
                r"(?:open|launch|start|run)\b",
                text,
            )
        )
        persian_command = any(
            phrase in text
            for phrase in (
                "باز کن",
                "بازش کن",
                "اجرا کن",
            )
        )
        return english_command or persian_command

    if tool_name == "forget_memory":
        return bool(
            re.search(r"\b(forget|delete\s+(?:the\s+)?memory|remove\s+(?:the\s+)?memory)\b", text)
            or any(
                phrase in text
                for phrase in (
                    "فراموش کن",
                    "از حافظه حذف",
                    "حافظه رو پاک",
                    "حافظه را پاک",
                )
            )
        )

    # Unknown future side-effecting tools require a future explicit policy.
    return False
