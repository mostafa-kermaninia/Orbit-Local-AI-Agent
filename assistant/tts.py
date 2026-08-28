from __future__ import annotations

import base64
import platform
import subprocess
import threading


class SystemTTS:
    """Interruptible local TTS.

    On Windows the default backend is a dedicated PowerShell/SAPI process. That
    is intentionally process-based: terminating speech is reliable, and a prior
    interruption cannot leave a shared pyttsx3 engine in a half-stopped state.
    Other platforms fall back to a fresh pyttsx3 engine per utterance.
    """

    def __init__(self, rate: int = 185, enabled: bool = True, backend: str = "auto") -> None:
        self.rate = int(rate)
        self.enabled = bool(enabled)
        self.backend = backend.strip().lower() or "auto"
        self._lock = threading.RLock()
        self._process: subprocess.Popen | None = None
        self._engine = None
        self._speaking = threading.Event()
        self.done_event = threading.Event()
        self.done_event.set()

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def _windows_sapi_command(self, text: str) -> list[str]:
        # SAPI rate is -10..10. Map the familiar pyttsx3-ish 185 baseline to 0.
        sapi_rate = max(-10, min(10, round((self.rate - 185) / 12)))
        escaped = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate={sapi_rate}; "
            f"$s.Speak('{escaped}');"
        )
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        return ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]

    def speak(self, text: str) -> None:
        text = " ".join(str(text).split()).strip()
        if not self.enabled or not text:
            return
        self.stop()
        self.done_event.clear()
        self._speaking.set()
        try:
            use_sapi = platform.system().lower() == "windows" and self.backend in {"auto", "sapi", "windows_sapi"}
            if use_sapi:
                proc = subprocess.Popen(
                    self._windows_sapi_command(text),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                with self._lock:
                    self._process = proc
                proc.wait()
                with self._lock:
                    if self._process is proc:
                        self._process = None
            else:
                import pyttsx3

                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                with self._lock:
                    self._engine = engine
                engine.say(text)
                engine.runAndWait()
                with self._lock:
                    if self._engine is engine:
                        self._engine = None
        finally:
            self._speaking.clear()
            self.done_event.set()

    def stop(self) -> None:
        proc = None
        engine = None
        with self._lock:
            proc, self._process = self._process, None
            engine, self._engine = self._engine, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=0.8)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        if engine is not None:
            try:
                engine.stop()
            except Exception:
                pass
        self._speaking.clear()
        self.done_event.set()
