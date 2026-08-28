from ui.sanitize import clean_log_line, tool_payload_for_log


def test_telegram_message_is_redacted_from_activity_stream():
    text = tool_payload_for_log(
        "send_telegram_message",
        {
            "contact": "Amir",
            "message": "private hello",
        },
    )

    assert "Amir" in text
    assert "private hello" not in text
    assert "REDACTED" in text


def test_web_source_content_is_not_dumped_to_activity_stream():
    text = tool_payload_for_log(
        "research_web",
        {
            "ok": True,
            "sources": [
                {
                    "rank": 1,
                    "title": "Example",
                    "content": "very private or huge fetched page body",
                    "fetch_ok": True,
                }
            ],
        },
    )

    assert "very private" not in text
    assert "Example" in text


def test_log_line_is_bounded():
    clean = clean_log_line("x" * 5_000, max_chars=200)
    assert len(clean) <= 200
