# Third-party notices

ORBIT depends on third-party software at runtime. Those projects are not owned by ORBIT and their upstream licenses remain in effect.

The Python packages below are installed from package indexes and are not vendored in this repository.

| Component | Role in ORBIT | Upstream license / note |
|---|---|---|
| CustomTkinter | Desktop UI widgets | MIT |
| NumPy | Audio/numeric arrays | BSD-3-Clause |
| python-sounddevice | Microphone/audio I/O | MIT |
| faster-whisper | Speech recognition runtime | MIT |
| Ollama Python client | Local model client | MIT |
| httpx | HTTP client | BSD-3-Clause |
| psutil | System telemetry / process inspection | BSD-3-Clause |
| pyttsx3 | Cross-platform TTS fallback | MPL-2.0 |
| yt-dlp | YouTube result resolution | Upstream project license applies |
| PyAutoGUI | Desktop automation | BSD-3-Clause |
| Pyperclip | Clipboard operations | BSD-style license |
| Beautiful Soup 4 | HTML parsing | MIT |

This table is a practical project-maintenance summary, not a substitute for the full upstream license texts. Verify dependency metadata again when creating a binary distribution.

## Models

Model weights are not covered by ORBIT's MIT License.

The recommended course model is:

- **Qwen2.5** — published upstream under Apache-2.0.

Other Qwen sizes, other Ollama models, Whisper variants, and future model releases can use different terms. Always verify the exact model/version before redistribution or commercial use.

## External applications and services

- **Telegram Desktop** is not bundled with ORBIT. ORBIT only automates the user's locally installed and logged-in desktop application.
- **YouTube**, web search engines, websites, browsers, and Ollama are external products/services and remain subject to their own terms.
- ORBIT does not imply sponsorship, endorsement, or affiliation with any named third-party product or organization.

## Redistribution

If you package ORBIT as an executable or installer, collect the license notices required by every bundled dependency and asset. A source-only repository that installs dependencies at runtime is different from redistributing those dependencies inside a binary bundle.
