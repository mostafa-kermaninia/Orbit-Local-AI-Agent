# ORBIT — Clean-room Local Voice Assistant

> **Working title only.** Rename the project before commercial publication and do a trademark check for your final brand.

ORBIT is a from-scratch educational local voice assistant built for teaching an end-to-end speech/agent pipeline:

```text
Microphone
   ↓
faster-whisper (STT)
   ↓
Ollama / Qwen (LLM + tool calls)
   ↓
Tool Registry ──→ Browser / YouTube / Telegram Desktop / Apps / Memory
   ↓
interruptible Windows SAPI / pyttsx3 TTS
   ↓
Speaker
```

The repository is an independent clean-room implementation with original source, prompts, UI drawing code, and project structure. See `ORIGIN.md`.

## Features

- Local LLM through Ollama (`qwen2.5` works as a lightweight starting point)
- Local speech recognition with faster-whisper
- Interruptible local TTS (Windows SAPI subprocess by default; pyttsx3 fallback)
- Natural-language tool calling

- Hands-free continuous listening: no LISTEN button required
- Best-effort voice barge-in: speaking over the assistant interrupts TTS and the new utterance becomes the next command
- Spoken startup greeting and explicit spoken success/failure feedback after tool calls
- Read-and-summarize web tools (`research_web`, `read_webpage`) in addition to visible browser search
- Rebuilt high-tech procedural HUD with rotating rings, signal bars, tool bus, CPU/RAM/network telemetry, and live state visualization
- Web search in the default browser
- YouTube video/topic opening
- **Telegram Desktop automation from the user's own desktop account**
- Visible Windows Start search → Telegram → contact search → paste message → Enter flow
- Safe application launcher with explicit allowlisted aliases
- CPU/RAM status tool
- Explicit local long-term memory
- Optional confirmation dialog for external-write actions
- Original procedural HUD UI drawn with CustomTkinter/Canvas — no copied images or assets

## 1. Prerequisites

- Windows 10/11 for the Telegram Desktop automation shown in the course
- Python 3.11 or 3.12 recommended
- Ollama installed and running
- Telegram Desktop installed and already logged in
- A microphone
- Internet once for downloading the selected Whisper model; after the model is cached, STT is local

Pull a local model:

```powershell
ollama pull qwen2.5
```

## 2. Windows setup

```powershell
git clone <YOUR-NEW-REPOSITORY-URL>
cd <YOUR-PROJECT-FOLDER>

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item config.example.json config.json
python scripts/check_setup.py
python main.py
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Configuration

Edit `config.json`.

Important fields:

```json
{
  "assistant_name": "ORBIT",
  "ollama_model": "qwen2.5",
  "stt_model": "small",
  "stt_language": "en",
  "continuous_listening": true,
  "auto_start_listening": true,
  "audio_interaction_mode": "half_duplex",
  "barge_in_enabled": false,
  "tts_backend": "auto",
  "confirm_external_actions": false,
  "telegram_launch_mode": "windows_search"
}
```

`confirm_external_actions` is `false` in the demo configuration so a clear voice command such as "send this message to Ali" proceeds without an extra popup. Set it to `true` if you want a human confirmation dialog before write actions.

### Microphone silence threshold

`silence_threshold` controls the simple RMS voice detector. If recording stops too early, lower it. If ambient noise keeps recording alive, raise it. Typical values are roughly `0.008` to `0.04`, depending on the microphone.

### Continuous listening and microphone gating

With `continuous_listening=true` and `auto_start_listening=true`, the assistant starts its hands-free loop automatically: listen → transcribe → think → speak → listen again. In the default `half_duplex` mode, the microphone is closed while TTS is speaking so the assistant cannot hear its own speaker output. Press **F2** to pause/resume. Press **Esc** to interrupt speech/reset audio; listening resumes automatically.

`barge_in_threshold` is intentionally higher than the normal silence threshold because the microphone can hear the assistant's speakers. If the assistant interrupts itself, raise this value (for example `0.08`–`0.12`). If it does not notice you speaking over it, lower it gradually. This is a teachable best-effort implementation, not full acoustic echo cancellation.

The default Windows TTS backend uses a separate SAPI process so speech can be terminated reliably. The assistant also speaks a startup message and every completed turn is forced to have a TTS-friendly final sentence.

## 4. Telegram Desktop flow

This project does **not** use Telegram Bot API credentials. It automates the user's installed Telegram Desktop application in a visible, teachable sequence.

When the user says:

```text
به مصطفی توی تلگرام پیام بده و بگو ده دقیقه دیگه می‌رسم
```

the pipeline is:

```text
Voice command
   ↓
LLM selects send_telegram_message(contact, message)
   ↓
Python presses Win
   ↓
Types "Telegram" in Windows Search
   ↓
Presses Enter and focuses Telegram Desktop
   ↓
Esc → Ctrl+F
   ↓
Pastes contact/chat name
   ↓
Selects first matching result
   ↓
Pastes the message
   ↓
Presses Enter to send
```

Clipboard paste is used instead of simulated typing for the contact/message so Persian and other Unicode text work reliably.

### Optional contact aliases

Aliases are not required. The assistant can search the contact name spoken by the user directly. Aliases are useful when the spoken nickname differs from the Telegram display name:

```json
{
  "telegram_contacts": {
    "دوستم": "Mostafa Test",
    "گروه دوره": "Speech Course Test Group"
  }
}
```

Then both of these can work:

```text
به Mostafa Test توی تلگرام پیام بده ...
به دوستم توی تلگرام پیام بده ...
```

### If Windows Search cannot find Telegram

Set the executable explicitly:

```json
{
  "telegram_desktop_executable": "C:\\Users\\YOUR_USER\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
  "telegram_launch_mode": "direct"
}
```

The code also checks common Telegram Desktop installation paths automatically as a fallback.

### Automation fail-safe

PyAutoGUI's fail-safe is enabled. If automation is behaving unexpectedly, move the mouse to the **top-left corner of the screen** to abort the current desktop automation.

For reliable demos:

- Keep Windows display scaling reasonably standard.
- Make sure Telegram Desktop is logged in.
- Use a distinctive test contact/chat name so the first search result is deterministic.
- Test the exact Telegram Desktop version before recording because UI behavior can change between releases.

## 5. Suggested demo commands

```text
What is my current CPU and RAM usage?

Search Python asyncio TaskGroup in my browser.

Research the latest Python asyncio TaskGroup documentation and summarize what you find.

Read https://docs.python.org/3/library/asyncio-task.html and give me a short summary.

Open a Python asyncio tutorial on YouTube.

Open Notepad.

Remember that my demo project is called Aurora.

What was my demo project called?

Send a Telegram message to my test contact saying: the final assistant test succeeded.
```

## 6. Project structure

```text
assistant/
  audio.py          microphone + faster-whisper
  config.py         typed configuration
  llm.py            Ollama conversation + tool loop
  memory.py         explicit JSON long-term memory
  orchestrator.py   voice/text pipeline coordinator
  tool_registry.py  schemas, handlers, confirmation boundary
  tools_factory.py  dependency wiring
  tts.py            replaceable offline TTS adapter

tools/
  browser.py        web search / URL opening
  youtube.py        YouTube resolution/opening
  telegram.py       Windows Telegram Desktop UI automation
  system.py         safe app allowlist + telemetry

ui/
  app.py            original procedural HUD UI

scripts/
  check_setup.py
```

## 7. Teaching points

For a course, teach the code in this order:

1. `main.py` — composition root
2. `assistant/config.py` — configuration boundary
3. `assistant/audio.py` — chunks, RMS silence detection, STT
4. `assistant/tool_registry.py` — contracts and controlled execution
5. `assistant/llm.py` — Ollama tool-call loop
6. `tools/browser.py` + `tools/youtube.py` — browser tools
7. `tools/telegram.py` — visible desktop automation + Unicode clipboard handling
8. `assistant/memory.py` — persistence
9. `assistant/orchestrator.py` — the complete data path
10. `ui/app.py` — keeping AI work off the GUI thread

That order follows the data flow rather than reading files alphabetically.

## 8. Security / reliability choices

- Telegram credentials are not required; the existing logged-in Telegram Desktop session is used.
- The Telegram tool only receives the target name and message text produced from the user's command.
- Apps can only be opened through configured aliases; there is no arbitrary shell tool.
- Normal URLs are limited to `http`/`https`.
- External-action confirmation can be turned on with `confirm_external_actions`.
- PyAutoGUI's fail-safe remains enabled.
- Keep `config.json` out of Git; `.gitignore` already excludes it.

## 9. Licensing / commercial-course checklist

The source files in this repository were written as a clean-room implementation for this project. Replace `<YOUR NAME>` in `LICENSE` before publishing.

Dependencies and model weights have their own licenses. `THIRD_PARTY_NOTICES.md` lists the main Python packages, but **you must verify the exact license of the Ollama model and any speech/TTS model weights you choose to redistribute or use commercially**.

You should select your own final product name and check trademarks before using that branding commercially.

## 10. Known limitations

- Desktop UI automation is inherently less stable than an official API and depends on the current Telegram/Windows UI.
- The Telegram implementation currently targets Windows.
- The first Telegram search result is selected; use distinctive names or configured aliases for course demos.
- `qwen2.5` tool selection depends on the exact local model/version; test it before recording.
- System TTS voice quality/language support depends on voices installed on the OS.
- YouTube sites change frequently; the tool falls back to a normal YouTube search page if direct first-result resolution fails.
- Barge-in is best-effort energy-based interruption; production voice agents normally add acoustic echo cancellation plus a dedicated VAD.
- Web extraction reads ordinary public HTML and can fail on paywalls, login-only pages, anti-bot systems, JavaScript-only apps, or non-HTML documents.
- The simple silence detector is deliberately teachable; production systems normally use a dedicated VAD.


## Reliable hands-free audio (v4)

The default interaction mode is `half_duplex`: the microphone listens automatically when the assistant is waiting for the user, but is closed while TTS is speaking. This prevents the assistant from detecting its own speaker output as a new user utterance. Press **Esc** to interrupt speech; continuous listening resumes automatically.

```json
"continuous_listening": true,
"auto_start_listening": true,
"audio_interaction_mode": "half_duplex",
"barge_in_enabled": false
```

The old threshold-based barge-in detector is still available for headphones or an audio path with acoustic echo cancellation:

```json
"audio_interaction_mode": "experimental_barge_in",
"barge_in_enabled": true
```

It is intentionally not the default because microphone thresholding alone cannot reliably distinguish the user's voice from the assistant's own loudspeaker audio.


## Final course-build Telegram behavior

The final build intentionally uses the V2 desktop flow that was validated on the target Windows machine: **Win → Telegram → Enter → Ctrl+F → contact → chat → message → Enter**. Telegram messages execute without a separate confirmation popup. ORBIT's manual interrupt shortcut is **F8**, leaving Escape free for Telegram navigation.
