from __future__ import annotations

import json
import sys
import types
from pathlib import Path

from assistant.config import AppConfig
from assistant.memory import MemoryStore
from assistant.tools_factory import build_registry
from tools.telegram import TelegramDesktopMessenger


class FakePyAutoGUI(types.SimpleNamespace):
    class FailSafeException(Exception):
        pass

    def __init__(self):
        super().__init__()
        self.calls = []
        self.FAILSAFE = False

    def press(self, key, **kwargs):
        self.calls.append(("press", key, kwargs))

    def write(self, text, **kwargs):
        self.calls.append(("write", text, kwargs))

    def hotkey(self, *keys):
        self.calls.append(("hotkey", keys))


class FakeClipboard(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.value = "old"
        self.history = []

    def copy(self, value):
        self.value = value
        self.history.append(value)

    def paste(self):
        return self.value


def test_final_v2_message_sequence(monkeypatch):
    fake_gui = FakePyAutoGUI()
    fake_clip = FakeClipboard()
    monkeypatch.setitem(sys.modules, "pyautogui", fake_gui)
    monkeypatch.setitem(sys.modules, "pyperclip", fake_clip)
    monkeypatch.setattr("tools.telegram.platform.system", lambda: "Windows")
    monkeypatch.setattr("tools.telegram.time.sleep", lambda *_: None)

    messenger = TelegramDesktopMessenger()
    monkeypatch.setattr(messenger, "_open_and_focus", lambda: (True, "Windows Search -> Telegram"))

    result = messenger.send("Amir", "hey, how are you?")
    assert result["ok"] is True
    assert ("press", "esc", {"presses": 2, "interval": 0.12}) in fake_gui.calls
    assert ("hotkey", ("ctrl", "f")) in fake_gui.calls
    assert "Amir" in fake_clip.history
    assert "hey, how are you?" in fake_clip.history
    assert ("press", "down", {}) in fake_gui.calls
    assert ("press", "enter", {}) in fake_gui.calls


def test_telegram_tool_is_classified_as_requiring_confirmation(tmp_path: Path):
    cfg = AppConfig(confirm_external_actions=True)
    memory = MemoryStore(tmp_path / "memory.json")
    registry, telegram, _launcher = build_registry(cfg, memory)
    spec = registry.spec("send_telegram_message")
    assert spec is not None
    assert spec.requires_confirmation is True
