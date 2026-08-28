# V3 upgrade — hands-free / voice feedback / research / HUD

## Voice loop
- Continuous listening can auto-start with no button press.
- After each completed response the assistant immediately listens again.
- Best-effort barge-in monitors the microphone while TTS is speaking; a strong new utterance stops TTS and becomes the next command.
- F2 pauses/resumes continuous listening; Esc interrupts/resets audio.

## TTS reliability
- Windows now defaults to process-based SAPI speech instead of a long-lived pyttsx3 engine.
- Speech can be terminated reliably during barge-in.
- Startup greeting is spoken.
- LLM instructions force a concise spoken final sentence after every tool result.
- Deterministic success/failure fallback exists if the local model produces a tool call but no final prose.

## Web
- `web_search`: visibly opens Google in the user's browser.
- `research_web`: searches the web, reads compact source text, returns it to the local LLM for synthesis.
- `read_webpage`: reads a user-provided public HTML URL for summarization/questions.
- `open_url`: opens an explicit URL.

## Existing tools
- `open_youtube`
- `send_telegram_message`
- `open_app`
- `get_system_status`
- `remember`
- `forget_memory`

## UI
- Full HUD redesign: rotating segmented rings, hex core, scanner, synthetic signal bars, live tool bus, CPU/RAM/network telemetry, state-reactive colors and activity stream.
- No external images/assets; all visuals are procedural.
