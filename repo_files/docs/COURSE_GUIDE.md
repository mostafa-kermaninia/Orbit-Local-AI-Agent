# Course Walkthrough

This document suggests an order for teaching ORBIT as the final project of a speech-processing course.

## 1. Start from the visible behavior

Show a short demo before opening the source code:

```text
Voice command
→ local transcription
→ local model decides on a tool
→ desktop action occurs
→ ORBIT reports the result by voice
```

A Telegram command is a strong opening because students can see the agent cross the boundary from language generation into a real operating-system action.

## 2. Read `main.py`

Teach the idea of a composition root:

```python
config → VoiceAssistant → OrbitUI → mainloop
```

Do not start by reading every import in the project.

## 3. Configuration

Open `assistant/config.py`.

Connect configuration to engineering decisions:

- model selection;
- Whisper size/language;
- sample rate;
- silence threshold;
- half-duplex audio;
- Telegram timing;
- app aliases.

## 4. Audio path

Open `assistant/audio.py`.

Relate it to earlier course concepts:

- 16 kHz sampling;
- audio chunks;
- amplitude / RMS;
- silence detection;
- Whisper.

Explain that production systems often use a dedicated VAD instead of a simple threshold.

## 5. Tool registry

Open `assistant/tool_registry.py`.

Key idea:

> The LLM does not execute Python. It requests a declared tool; Python validates and executes the action.

Show a schema and a handler.

## 6. Local LLM and tool loop

Open `assistant/llm.py`.

Trace:

```text
user text
→ Ollama chat
→ possible tool call
→ Python tool result
→ result returned to model
→ final spoken response
```

Point out the explicit guard that prevents a failed web-research call from being presented as verified online research.

## 7. Browser and research

Open `tools/browser.py`.

Contrast:

- `web_search`: visible browser navigation;
- `research_web`: visible search + source tabs + background text extraction;
- `read_webpage`: one specific URL.

This is a good place to discuss reliability versus screen-coordinate automation.

## 8. Telegram Desktop

Open `tools/telegram.py`.

Trace the actual visible sequence.

Discuss:

- clipboard and Unicode;
- window focus;
- timing;
- PyAutoGUI fail-safe;
- why desktop automation is inherently less stable than an API.

## 9. Memory

Open `assistant/memory.py`.

Emphasize:

```text
model parameters ≠ personal mutable memory
```

Persistent facts are stored outside the model and reintroduced as context.

## 10. Orchestrator

Open `assistant/orchestrator.py`.

Now the students already know the pieces, so the orchestrator is easier to understand.

Show the state flow:

```text
LISTENING → TRANSCRIBING → THINKING → SPEAKING → LISTENING
```

Explain why the default project gates the microphone during TTS.

## 11. UI last

Open `ui/app.py` last.

The UI is a view of the system state; it is not the intelligence itself.

Show how:

- state events;
- tool events;
- telemetry;
- transcription;
- assistant output;

are reflected on screen.

## Final demo sequence

1. CPU/RAM status.
2. Visible browser search.
3. Multi-source research.
4. YouTube.
5. Memory.
6. Telegram Desktop.
7. Manual `F8` interruption.

This order gradually increases the amount of real-world agency.
