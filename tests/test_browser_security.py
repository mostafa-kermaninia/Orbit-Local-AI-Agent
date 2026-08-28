import pytest

from tools import browser


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:11434",
        "http://localhost:8080",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "http://169.254.169.254",
        "http://[::1]/",
    ],
)
def test_private_or_local_webpage_targets_are_blocked(url):
    with pytest.raises(ValueError):
        browser._validate_url(url, public_fetch=True)


def test_browser_open_url_can_still_open_local_user_requested_url(monkeypatch):
    opened = []
    monkeypatch.setattr(
        browser.webbrowser,
        "open_new_tab",
        lambda url: opened.append(url) or True,
    )

    result = browser.open_url("http://127.0.0.1:11434")
    assert result["ok"] is True
    assert opened == ["http://127.0.0.1:11434"]
