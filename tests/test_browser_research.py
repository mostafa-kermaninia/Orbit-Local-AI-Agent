from tools import browser


def _candidate(index: int) -> dict[str, str]:
    return {
        "title": f"Source {index}",
        "url": f"https://example{index}.com/article",
        "snippet": f"Snippet {index}",
    }


def test_research_reports_failure_when_no_page_is_readable(monkeypatch):
    monkeypatch.setattr(
        browser,
        "_search_candidates",
        lambda *_args, **_kwargs: (
            [_candidate(1), _candidate(2)],
            "Bing",
            [],
        ),
    )
    monkeypatch.setattr(
        browser,
        "_validate_url",
        lambda url, public_fetch: url,
    )
    monkeypatch.setattr(
        browser,
        "read_webpage",
        lambda *_args, **_kwargs: {
            "ok": False,
            "error": "blocked",
        },
    )

    result = browser.research_web(
        "test",
        visual=False,
        max_results=2,
    )

    assert result["ok"] is False
    assert result["evidence_level"] == "snippets_only"
    assert result["readable_source_count"] == 0


def test_research_caps_total_evidence_chars(monkeypatch):
    monkeypatch.setattr(
        browser,
        "_search_candidates",
        lambda *_args, **_kwargs: (
            [_candidate(1), _candidate(2), _candidate(3)],
            "Bing",
            [],
        ),
    )
    monkeypatch.setattr(
        browser,
        "_validate_url",
        lambda url, public_fetch: url,
    )

    def fake_page(*_args, char_limit=4000, **_kwargs):
        return {
            "ok": True,
            "content": "x" * char_limit,
        }

    monkeypatch.setattr(
        browser,
        "read_webpage",
        fake_page,
    )

    result = browser.research_web(
        "test",
        visual=False,
        max_results=3,
        char_limit=4_000,
        total_char_limit=5_000,
    )

    assert result["ok"] is True
    assert result["evidence_chars"] <= 5_000
