from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AppConfig:
    assistant_name: str = "ORBIT"
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5"
    system_language: str = "en"

    stt_model: str = "small"
    stt_language: str = "en"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    sample_rate: int = 16_000
    audio_chunk: int = 1024
    silence_threshold: float = 0.018
    silence_seconds: float = 0.75
    max_record_seconds: float = 20.0

    # Hands-free operation.
    continuous_listening: bool = True
    auto_start_listening: bool = True
    # Reliable default: keep the microphone closed while TTS is playing.
    # This prevents the assistant from hearing its own speakers.
    audio_interaction_mode: str = "half_duplex"  # half_duplex | experimental_barge_in
    barge_in_enabled: bool = False
    # Barge-in needs a higher threshold than normal listening because the mic can
    # hear the assistant's own speakers. Tune this for the room/microphone.
    barge_in_threshold: float = 0.065
    barge_in_silence_seconds: float = 0.55
    barge_in_grace_seconds: float = 0.75

    tts_enabled: bool = True
    tts_rate: int = 185
    tts_backend: str = "auto"  # auto -> Windows SAPI subprocess on Windows, pyttsx3 elsewhere
    speak_startup_greeting: bool = True
    startup_greeting: str = "ORBIT online. Local systems are ready. I'm listening."
    speak_tool_results: bool = True
    confirm_external_actions: bool = False

    web_fetch_timeout_seconds: float = 12.0
    web_research_results: int = 5
    web_page_char_limit: int = 7000

    # Telegram Desktop automation. Aliases are optional: when no alias matches,
    # the exact contact string produced from the user's command is searched.
    telegram_desktop_executable: str = ""
    telegram_launch_mode: str = "windows_search"
    telegram_contacts: dict[str, str] = field(default_factory=dict)
    telegram_launch_wait_seconds: float = 3.0
    telegram_search_wait_seconds: float = 1.6
    telegram_chat_wait_seconds: float = 0.9

    app_aliases: dict[str, str] = field(default_factory=lambda: {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
    })


def _merge_dataclass(default: AppConfig, raw: dict[str, Any]) -> AppConfig:
    allowed = set(asdict(default))
    clean = {k: v for k, v in raw.items() if k in allowed}
    return AppConfig(**{**asdict(default), **clean})


def load_config(path: str | Path = "config.json") -> AppConfig:
    path = Path(path)
    default = AppConfig()
    if not path.exists():
        path.write_text(json.dumps(asdict(default), ensure_ascii=False, indent=2), encoding="utf-8")
        return default
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("config root must be an object")
        return _merge_dataclass(default, raw)
    except Exception as exc:
        raise RuntimeError(f"Could not read {path}: {exc}") from exc


def save_config(config: AppConfig, path: str | Path = "config.json") -> None:
    Path(path).write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
