# Changelog

All notable changes to ORBIT are documented here.

The project follows a simple semantic versioning scheme for course releases.

## [1.0.0] - 2026-08-28

### Added

- Local STT with faster-whisper.
- Local LLM inference through Ollama.
- Natural-language tool calling and tool-result feedback.
- Continuous hands-free listening.
- Reliable half-duplex microphone gating during TTS.
- Interruptible Windows SAPI TTS with pyttsx3 fallback.
- Visible web search and multi-source web research.
- Public webpage reading and summarization.
- YouTube result opening with search fallback.
- Telegram Desktop message automation using the local logged-in session.
- Safe allowlisted application launcher.
- CPU/RAM telemetry.
- Explicit JSON-based long-term memory.
- Procedural CustomTkinter/Tk Canvas HUD.
- Setup checker, unit tests, CI, issue templates, and project documentation.

### Reliability decisions

- Default audio mode is `half_duplex`; experimental threshold-based barge-in is disabled.
- `F8` is the manual interrupt shortcut, leaving `Esc` available to Telegram navigation.
- Telegram demo behavior uses visible Windows Search and clipboard-safe Unicode input.
- Web research returns fetched evidence to the local LLM and guards against pretending failed research succeeded.
