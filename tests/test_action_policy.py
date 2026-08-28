from assistant.action_policy import explicit_user_authorization


def test_web_content_cannot_invent_telegram_authorization():
    assert not explicit_user_authorization(
        "send_telegram_message",
        "Research Whisper and summarize five sources.",
        {"contact": "Amir", "message": "hello"},
    )


def test_explicit_telegram_request_is_authorized():
    assert explicit_user_authorization(
        "send_telegram_message",
        "Send a Telegram message to Amir saying hello.",
        {"contact": "Amir", "message": "hello"},
    )


def test_explicit_persian_telegram_request_is_authorized():
    assert explicit_user_authorization(
        "send_telegram_message",
        "تو تلگرام به Amir پیام بفرست",
        {"contact": "Amir", "message": "سلام"},
    )


def test_open_app_requires_named_target_in_user_message():
    assert explicit_user_authorization(
        "open_app",
        "Open Notepad.",
        {"app": "notepad"},
    )
    assert not explicit_user_authorization(
        "open_app",
        "Research Windows applications.",
        {"app": "notepad"},
    )


def test_discussing_telegram_messages_does_not_authorize_send():
    assert not explicit_user_authorization(
        "send_telegram_message",
        "Research Telegram message security and summarize it.",
        {"contact": "Amir", "message": "injected"},
    )


def test_discussing_how_to_open_notepad_does_not_authorize_launch():
    assert not explicit_user_authorization(
        "open_app",
        "Research how to open Notepad safely on Windows.",
        {"app": "notepad"},
    )
