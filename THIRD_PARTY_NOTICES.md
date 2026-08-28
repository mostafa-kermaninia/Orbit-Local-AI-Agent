# Third-party notices

ORBIT's MIT License covers the ORBIT source code in this repository. Runtime dependencies, model weights, applications, and online services remain separate works with their own upstream licenses and terms.

## Python dependencies

The repository installs these packages from the Python package ecosystem rather than vendoring their source:

| Component | Role |
|---|---|
| CustomTkinter | Desktop UI widgets |
| NumPy | Numeric/audio arrays |
| python-sounddevice | Microphone/audio I/O |
| faster-whisper | Speech-recognition runtime |
| Ollama Python client | Local-model client |
| httpx | HTTP client |
| psutil | System telemetry |
| pyttsx3 | TTS fallback |
| yt-dlp | YouTube result resolution |
| PyAutoGUI | Desktop automation |
| Pyperclip | Clipboard operations |
| Beautiful Soup 4 | HTML parsing |

Refer to each installed package's upstream metadata/license for the exact version you redistribute. A source repository that installs dependencies at runtime is different from bundling those dependencies into an executable/installer.

## Recommended model

The course/repository default is:

```text
qwen2.5:7b
```

Qwen2.5 7B is published upstream under the Apache License 2.0. Model weights are not covered by ORBIT's MIT License.

If you change model family or size, verify the exact model's license independently before commercial redistribution.

## External applications/services

- Telegram Desktop is not bundled with ORBIT. ORBIT automates the user's locally installed/logged-in application.
- YouTube, web search engines, websites, browsers, Ollama, Qwen, Whisper, and other named products/services are owned by their respective parties.
- ORBIT does not imply sponsorship, endorsement, or affiliation with those third parties.

## Binary redistribution

If you later package ORBIT as an installer/executable, perform a fresh dependency-license inventory for the exact bundled versions and include all required notices/licenses in the distribution.
