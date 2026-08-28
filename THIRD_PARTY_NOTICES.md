# Third-party notices

This project imports third-party packages at runtime; their code is not vendored in this repository. Keep their license notices when redistributing packaged applications.

- **Ollama Python client** — MIT License.
- **faster-whisper** — MIT License.
- **python-sounddevice** — MIT License.
- **CustomTkinter** — MIT License (current upstream repository).
- **pyttsx3** — MPL-2.0.
- **httpx** — BSD-3-Clause.
- **psutil** — BSD-3-Clause.
- **yt-dlp** — Unlicense for the PyPI source/wheel; optional dependencies can have their own licenses.
- **NumPy** — BSD-3-Clause.
- **PyAutoGUI** — BSD-3-Clause.
- **Pyperclip** — BSD-3-Clause.

The Ollama model you select and any speech/TTS model weights are separate works and can have their own licenses. Verify the exact model license before commercial use. In particular, Qwen2.5 3B/72B use a different Qwen license, while the other Qwen2.5 sizes are published under Apache-2.0 according to the Qwen/Ollama model documentation.

Telegram Desktop is a separate third-party application; this project does not bundle Telegram and simply automates the user's locally installed application.

This file is a practical checklist, not legal advice.
