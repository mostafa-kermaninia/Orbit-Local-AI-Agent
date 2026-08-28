# Troubleshooting

This page collects common setup problems seen on Windows course machines.

## `pip` reports `ConnectionResetError 10054`

Typical output:

```text
An existing connection was forcibly closed by the remote host
```

This is usually a network/TLS path problem, not evidence that the package does not exist.

Try:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the network path is unstable, retry on a different connection or VPN permitted in your environment.

Do not repeatedly delete a working virtual environment just because PyPI temporarily reset the connection.

## Whisper appears stuck on `TRANSCRIBING` the first time

`faster-whisper` lazily loads/downloads the selected model on first use.

Test loading directly:

```powershell
python -c "from faster_whisper import WhisperModel; print('Loading...'); WhisperModel('small', device='cpu', compute_type='int8'); print('READY')"
```

The first run can take much longer than later runs because model files must be downloaded and cached.

## Hugging Face download is slow

You can pre-download the model:

```powershell
hf download Systran/faster-whisper-small
```

Public models can be downloaded without a token, but authenticated Hugging Face requests can have better rate limits.

## `Unable to open file 'model.bin'`

First verify you are running the expected Python environment:

```powershell
python -c "import sys; print(sys.executable); print(sys.version)"
python -c "import faster_whisper; print(faster_whisper.__file__)"
```

Both paths should belong to the active `.venv`.

If `faster_whisper` is unexpectedly loading from another Python installation under `AppData\Roaming`, recreate the venv and avoid user-site packages:

```powershell
$env:PYTHONNOUSERSITE="1"
```

Then reinstall dependencies inside that venv.

A corrupted/incomplete Hugging Face model cache can also require re-downloading the affected model file.

## ORBIT hears its own TTS

Use the default configuration:

```json
"audio_interaction_mode": "half_duplex",
"barge_in_enabled": false
```

This gates the microphone while the assistant is speaking.

Threshold-only barge-in without acoustic echo cancellation can confuse loudspeaker audio with real user speech.

## ORBIT sometimes shows text but does not speak

Confirm:

```json
"tts_enabled": true,
"tts_backend": "auto"
```

On Windows, the preferred path uses SAPI. Test that Windows has a working system voice.

## Telegram opens but the contact is not selected

The current demo flow chooses the first matching search result.

Recommendations:

- use a distinctive test contact/chat name;
- test the exact Telegram Desktop version before recording;
- increase the configured Telegram wait values on slow machines;
- use a contact alias if speech recognition produces a nickname different from the Telegram display name.

## Telegram action behaves unexpectedly

Move the mouse to the **top-left corner** to trigger PyAutoGUI's fail-safe.

ORBIT uses `F8` for manual interrupt so Telegram can use `Esc` internally.

## Windows Search does not find Telegram

Set the executable explicitly:

```json
{
  "telegram_launch_mode": "direct",
  "telegram_desktop_executable": "C:\\Users\\YOUR_USER\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe"
}
```

## Web research reports TLS / SSL EOF errors

The web tool has multiple network paths/fallbacks, but VPNs, proxies, antivirus TLS inspection, and ISP paths can still terminate HTTPS sessions.

Verify basic HTTPS access and retry on a stable network.

The assistant should report failed research rather than presenting internal model knowledge as verified online research.

## Web research cannot read a site

Expected limitations include:

- login-only pages;
- paywalls;
- CAPTCHAs;
- anti-bot systems;
- JavaScript-only apps;
- unsupported document types such as some PDFs.

Use a normal public HTML source for the course demo.

## Ollama model is not found

Check:

```powershell
ollama list
```

For the recommended course build:

```powershell
ollama pull qwen2.5:7b
```

Then:

```powershell
python scripts/check_setup.py
```

## Python environment sanity check

When debugging dependency confusion, always run:

```powershell
python -c "import sys; print(sys.executable); print(sys.version)"
python -m pip --version
```

Both should point to the same virtual environment.
