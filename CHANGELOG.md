# Changelog

All notable ORBIT course releases are documented here.

## [1.0.0] - 2026-08-28

### Core agent

- Local faster-whisper speech recognition.
- Ollama/Qwen local reasoning and tool calling.
- Continuous half-duplex voice loop.
- Interruptible TTS and F8 manual interruption.
- Explicit JSON long-term memory.
- Tool registry and spoken tool-result feedback.

### Tools

- Visible browser search.
- Visible five-source web research with bounded evidence extraction.
- Specific public webpage reading.
- YouTube opening/search fallback.
- Telegram Desktop automation.
- Safe configured app aliases.
- System telemetry.

### Safety and reliability

- Qwen default pinned to `qwen2.5:7b`.
- Public config enables confirmation for side-effecting tools.
- Separate course/demo config can intentionally disable confirmation dialogs.
- Webpage reader blocks loopback/private/link-local destinations.
- Redirect targets are validated before fetch.
- Web responses and research evidence are size-bounded.
- Retrieved web/tool content is explicitly treated as untrusted data.
- Activity Stream tool payloads are redacted and truncated.
- Telegram distinguishes local send-action completion from independent delivery verification.
- Atomic memory writes preserve corrupt files instead of silently overwriting them.
- Continuous listening uses per-session stop events to avoid rapid F2 restart races.

### Repository quality

- Windows CI for Python 3.11 and 3.12.
- Critical Ruff checks and expanded unit tests.
- Security, privacy, support, roadmap, provenance, contribution, and conduct documentation.
- GitHub issue/PR templates, CODEOWNERS, and Dependabot configuration.
