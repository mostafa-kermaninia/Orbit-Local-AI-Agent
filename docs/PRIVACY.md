# Privacy Model

ORBIT is **local-first**, not fully offline.

The speech-recognition, local-LLM, memory, telemetry, and default TTS paths can run on the user's computer. Network tools intentionally contact external services when the user invokes them.

| Component | Leaves the device by default? | Notes |
|---|---:|---|
| `faster-whisper` STT | No | Audio is processed locally after model files are present. |
| Ollama / Qwen | No | Inference is sent to the configured local Ollama host. |
| Local memory | No | Stored in `data/memory.json`. |
| CPU/RAM telemetry | No | Read through `psutil`. |
| Windows SAPI TTS | No external ORBIT service | Uses the installed Windows speech subsystem. |
| Web Search | Yes | The query is sent to the selected search engine in the browser. |
| Web Research | Yes | Search queries and HTTP requests are sent to search engines/source sites. |
| YouTube | Yes | YouTube is contacted to resolve/open content. |
| Telegram Desktop | Yes | Telegram Desktop uses the user's existing Telegram connection/account. |

## Activity Stream

ORBIT redacts message bodies, webpage content, memory values, credentials-like fields, and large tool payloads before placing tool data in the on-screen Activity Stream.

The UI log is still visible to anyone who can see the screen. Do not demonstrate private contacts or sensitive material in a public recording.

## Repository hygiene

The following are ignored by Git:

- `config.json`
- `.env*`
- local memory
- common session files
- audio recordings
- logs
- virtual environments

Never commit credentials, Telegram session data, personal recordings, or a private `config.json`.

## Web content

Retrieved webpage content is treated as untrusted data. ORBIT's system policy tells the model not to follow instructions embedded in fetched pages; a deterministic authorization guard prevents retrieved content from inventing current side-effecting actions; and the webpage reader blocks loopback/private/local-network destinations.
