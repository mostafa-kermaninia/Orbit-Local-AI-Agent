from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

import httpx


REQUIRED_IMPORTS = {
    "customtkinter": "customtkinter",
    "numpy": "numpy",
    "sounddevice": "sounddevice",
    "faster_whisper": "faster-whisper",
    "ollama": "ollama",
    "httpx": "httpx",
    "psutil": "psutil",
    "pyttsx3": "pyttsx3",
    "yt_dlp": "yt-dlp",
    "pyautogui": "pyautogui",
    "pyperclip": "pyperclip",
    "bs4": "beautifulsoup4",
}


def status(label: str, ok: bool, detail: str = "") -> None:
    marker = "OK" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{marker:4}] {label}{suffix}")


def warn(label: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"[WARN] {label}{suffix}")


def _load_config() -> dict:
    path = Path("config.json")
    if not path.exists():
        warn(
            "config.json",
            "not found; copy config.example.json or config.course.example.json",
        )
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        status("config.json", False, str(exc))
        raise SystemExit(1)

    if not isinstance(data, dict):
        status("config.json", False, "root must be a JSON object")
        raise SystemExit(1)

    status("config.json", True, str(path.resolve()))
    return data


def _model_matches(installed: str, configured: str) -> bool:
    installed = installed.strip()
    configured = configured.strip()

    if installed == configured:
        return True

    if ":" not in configured and installed == configured + ":latest":
        return True

    return False


def main() -> int:
    failures = 0

    py_ok = (3, 11) <= sys.version_info[:2] <= (3, 12)
    status(
        "Python",
        py_ok,
        f"{sys.version.split()[0]} ({sys.executable})",
    )
    if not py_ok:
        failures += 1

    status(
        "Platform",
        platform.system().lower() == "windows",
        f"{platform.system()} {platform.release()}",
    )
    if platform.system().lower() != "windows":
        warn(
            "Platform support",
            "the full desktop automation/UI course build targets Windows 10/11",
        )

    missing: list[str] = []
    for import_name, package_name in REQUIRED_IMPORTS.items():
        if importlib.util.find_spec(import_name) is None:
            missing.append(package_name)

    if missing:
        status(
            "Python dependencies",
            False,
            "missing: " + ", ".join(sorted(missing)),
        )
        failures += 1
    else:
        status(
            "Python dependencies",
            True,
            "all required imports found",
        )

    config = _load_config()
    host = str(
        config.get(
            "ollama_host",
            "http://127.0.0.1:11434",
        )
    ).rstrip("/")
    model = str(
        config.get(
            "ollama_model",
            "qwen2.5:7b",
        )
    )

    ollama_executable = shutil.which("ollama")
    if ollama_executable:
        status(
            "Ollama executable",
            True,
            ollama_executable,
        )
    else:
        status(
            "Ollama executable",
            False,
            "not found in PATH",
        )
        failures += 1

    try:
        response = httpx.get(
            host + "/api/tags",
            timeout=4,
        )
        response.raise_for_status()
        names = [
            str(item.get("name") or "")
            for item in response.json().get("models", [])
            if item.get("name")
        ]

        status("Ollama server", True, host)

        model_ok = any(
            _model_matches(name, model)
            for name in names
        )
        status(
            "Configured model",
            model_ok,
            f"{model}; installed: {', '.join(names) or 'none'}",
        )
        if not model_ok:
            failures += 1
    except Exception as exc:
        status("Ollama server", False, str(exc))
        failures += 1

    if config.get("confirm_external_actions") is False:
        warn(
            "External-action confirmations",
            "disabled; appropriate for an instructor-controlled demo, not the safest public default",
        )

    warn(
        "Telegram Desktop",
        "not launched by this checker; test with a non-sensitive contact before recording",
    )

    print()
    if failures:
        print(
            f"Setup check finished with {failures} blocking problem(s)."
        )
        return 1

    print("Setup check passed. ORBIT is ready to launch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
