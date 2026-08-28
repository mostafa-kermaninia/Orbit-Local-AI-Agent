from __future__ import annotations

import threading
import time
from collections.abc import Callable

from assistant.audio import CaptureResult, SpeechCapture, WhisperSTT
from assistant.config import AppConfig
from assistant.llm import LocalAgentLLM
from assistant.memory import MemoryStore
from assistant.tool_registry import ToolSpec
from assistant.tools_factory import build_registry
from assistant.tts import SystemTTS


class VoiceAssistant:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.memory = MemoryStore()
        self.registry, self.telegram, self.launcher = build_registry(
            config,
            self.memory,
        )
        self.llm = LocalAgentLLM(
            config,
            self.registry,
            self.memory,
        )

        self.capture = SpeechCapture(
            sample_rate=config.sample_rate,
            chunk_size=config.audio_chunk,
            silence_threshold=config.silence_threshold,
            silence_seconds=config.silence_seconds,
            max_seconds=config.max_record_seconds,
        )
        self.barge_capture = SpeechCapture(
            sample_rate=config.sample_rate,
            chunk_size=config.audio_chunk,
            silence_threshold=config.barge_in_threshold,
            silence_seconds=config.barge_in_silence_seconds,
            max_seconds=config.max_record_seconds,
        )
        self.stt = WhisperSTT(
            model_name=config.stt_model,
            device=config.stt_device,
            compute_type=config.stt_compute_type,
            language=config.stt_language,
        )
        self.tts = SystemTTS(
            rate=config.tts_rate,
            enabled=config.tts_enabled,
            backend=config.tts_backend,
        )

        self._busy_lock = threading.Lock()
        self._continuous_lock = threading.RLock()
        self._active_continuous_stop: threading.Event | None = None

    def cancel_audio(self) -> None:
        self.capture.cancel()
        self.barge_capture.cancel()
        self.tts.stop()

    def stop_continuous(self) -> None:
        with self._continuous_lock:
            stop_event = self._active_continuous_stop

        if stop_event is not None:
            stop_event.set()

        self.cancel_audio()

    def _answer(
        self,
        text: str,
        *,
        confirm: Callable[[ToolSpec, dict], bool] | None,
        on_tool: Callable[[str, dict], None] | None,
        on_tool_result: Callable[[str, dict], None] | None,
    ) -> str:
        return self.llm.answer(
            text,
            contact_aliases=self.telegram.contact_aliases(),
            app_aliases=self.launcher.names(),
            confirm=(
                confirm
                if self.config.confirm_external_actions
                else None
            ),
            on_tool=on_tool,
            on_tool_result=on_tool_result,
        )

    def process_text(
        self,
        text: str,
        *,
        confirm: Callable[[ToolSpec, dict], bool] | None = None,
        on_state: Callable[[str], None] | None = None,
        on_tool: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, dict], None] | None = None,
    ) -> str:
        with self._busy_lock:
            if on_state:
                on_state("THINKING")

            answer = self._answer(
                text,
                confirm=confirm,
                on_tool=on_tool,
                on_tool_result=on_tool_result,
            )

            if on_state:
                on_state("SPEAKING")
            self.tts.speak(answer)

            if on_state:
                on_state("IDLE")

            return answer

    def _transcribe_capture(
        self,
        captured: CaptureResult,
        *,
        on_state: Callable[[str], None] | None,
        on_transcript: Callable[[str], None] | None,
    ) -> str:
        if not captured.speech_detected:
            return ""

        if on_state:
            on_state("TRANSCRIBING")

        text = self.stt.transcribe(captured.audio)

        if text and on_transcript:
            on_transcript(text)

        return text

    def listen_and_process(
        self,
        *,
        confirm: Callable[[ToolSpec, dict], bool] | None = None,
        on_state: Callable[[str], None] | None = None,
        on_transcript: Callable[[str], None] | None = None,
        on_tool: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, dict], None] | None = None,
    ) -> tuple[str, str]:
        with self._busy_lock:
            if on_state:
                on_state("LISTENING")

            captured = self.capture.listen_once(
                wait_timeout=30.0,
            )
            text = self._transcribe_capture(
                captured,
                on_state=on_state,
                on_transcript=on_transcript,
            )

            if not text:
                if on_state:
                    on_state("IDLE")
                return "", ""

            if on_state:
                on_state("THINKING")

            answer = self._answer(
                text,
                confirm=confirm,
                on_tool=on_tool,
                on_tool_result=on_tool_result,
            )

            if on_state:
                on_state("SPEAKING")

            self.tts.speak(answer)

            if on_state:
                on_state("IDLE")

            return text, answer

    def _speak_and_watch_for_barge_in(
        self,
        answer: str,
    ) -> CaptureResult | None:
        """Speak using half-duplex or the optional experimental barge-in mode."""
        if not self.config.tts_enabled:
            return None

        mode = str(
            getattr(
                self.config,
                "audio_interaction_mode",
                "half_duplex",
            )
        ).strip().lower()

        if (
            mode != "experimental_barge_in"
            or not self.config.barge_in_enabled
        ):
            self.tts.speak(answer)
            return None

        speech_thread = threading.Thread(
            target=self.tts.speak,
            args=(answer,),
            name="tts-utterance",
            daemon=True,
        )
        speech_thread.start()

        deadline = time.monotonic() + 0.5
        while (
            time.monotonic() < deadline
            and not self.tts.is_speaking
            and speech_thread.is_alive()
        ):
            time.sleep(0.015)

        if not speech_thread.is_alive():
            return None

        interruption = self.barge_capture.listen_once(
            threshold=self.config.barge_in_threshold,
            silence_seconds=self.config.barge_in_silence_seconds,
            ignore_first_seconds=self.config.barge_in_grace_seconds,
            stop_when=self.tts.done_event,
        )

        if interruption.speech_detected:
            self.tts.stop()
            speech_thread.join(timeout=1.0)
            return interruption

        speech_thread.join(timeout=1.0)
        return None

    def run_continuous(
        self,
        *,
        confirm: Callable[[ToolSpec, dict], bool] | None = None,
        on_state: Callable[[str], None] | None = None,
        on_transcript: Callable[[str], None] | None = None,
        on_answer: Callable[[str], None] | None = None,
        on_tool: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, dict], None] | None = None,
        on_system: Callable[[str], None] | None = None,
    ) -> None:
        """Hands-free listen → think → speak loop.

        Default half-duplex behavior opens the microphone only while LISTENING.
        After TTS finishes, listening resumes automatically. F8 is the manual
        interrupt key in the desktop UI.

        Each run owns its own stop Event. A rapid stop/start cannot reactivate
        an older listening loop.
        """
        session_stop = threading.Event()

        with self._continuous_lock:
            previous_stop = self._active_continuous_stop
            if previous_stop is not None:
                previous_stop.set()
            self._active_continuous_stop = session_stop

        pending_capture: CaptureResult | None = None

        try:
            if (
                self.config.speak_startup_greeting
                and self.config.startup_greeting.strip()
                and not session_stop.is_set()
            ):
                if on_state:
                    on_state("SPEAKING")
                if on_answer:
                    on_answer(self.config.startup_greeting)
                self.tts.speak(self.config.startup_greeting)

            while not session_stop.is_set():
                try:
                    if pending_capture is None:
                        if on_state:
                            on_state("LISTENING")
                        captured = self.capture.listen_once(
                            stop_when=session_stop,
                        )
                    else:
                        captured = pending_capture
                        pending_capture = None

                    if session_stop.is_set():
                        break

                    text = self._transcribe_capture(
                        captured,
                        on_state=on_state,
                        on_transcript=on_transcript,
                    )
                    if not text:
                        continue

                    if on_state:
                        on_state("THINKING")

                    answer = self._answer(
                        text,
                        confirm=confirm,
                        on_tool=on_tool,
                        on_tool_result=on_tool_result,
                    )

                    if on_answer:
                        on_answer(answer)

                    if on_state:
                        on_state("SPEAKING")

                    interruption = self._speak_and_watch_for_barge_in(
                        answer
                    )

                    if session_stop.is_set():
                        break

                    if (
                        interruption is not None
                        and interruption.speech_detected
                    ):
                        if on_system:
                            on_system(
                                "Barge-in detected. Previous speech interrupted; "
                                "processing the new utterance."
                            )
                        if on_state:
                            on_state("INTERRUPTED")
                        pending_capture = interruption
                    elif on_state:
                        on_state("LISTENING")

                except Exception as exc:
                    if session_stop.is_set():
                        break

                    if on_system:
                        on_system(f"Voice loop error: {exc}")
                    if on_state:
                        on_state("ERROR")
                    time.sleep(0.35)
        finally:
            with self._continuous_lock:
                if self._active_continuous_stop is session_stop:
                    self._active_continuous_stop = None

            if on_state:
                on_state("IDLE")
