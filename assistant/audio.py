from __future__ import annotations

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass

import numpy as np
import sounddevice as sd


@dataclass(slots=True)
class CaptureResult:
    audio: np.ndarray
    duration: float
    speech_detected: bool


class SpeechCapture:
    """Record one utterance using a simple RMS detector.

    The recorder can wait indefinitely for speech, then enforce a maximum speech
    duration. A short pre-roll keeps the first consonant from being clipped.
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        chunk_size: int = 1024,
        silence_threshold: float = 0.018,
        silence_seconds: float = 0.9,
        max_seconds: float = 20.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.silence_seconds = silence_seconds
        self.max_seconds = max_seconds
        self._stop = threading.Event()

    def cancel(self) -> None:
        self._stop.set()

    def listen_once(
        self,
        *,
        threshold: float | None = None,
        silence_seconds: float | None = None,
        wait_timeout: float | None = None,
        ignore_first_seconds: float = 0.0,
        stop_when: threading.Event | None = None,
    ) -> CaptureResult:
        self._stop.clear()
        threshold = self.silence_threshold if threshold is None else float(threshold)
        silence_seconds = self.silence_seconds if silence_seconds is None else float(silence_seconds)

        chunks: queue.Queue[np.ndarray] = queue.Queue(maxsize=128)
        frames: list[np.ndarray] = []
        pre_roll: deque[np.ndarray] = deque(maxlen=max(2, int(0.22 * self.sample_rate / self.chunk_size)))
        speech_started = False
        silent_for = 0.0
        waiting_started = time.monotonic()
        speech_started_at: float | None = None

        def callback(indata, frames_count, time_info, status):  # noqa: ANN001
            del frames_count, time_info, status
            try:
                chunks.put_nowait(indata[:, 0].copy())
            except queue.Full:
                pass

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=callback,
        ):
            while not self._stop.is_set():
                if stop_when is not None and stop_when.is_set():
                    break
                now = time.monotonic()
                if not speech_started and wait_timeout is not None and now - waiting_started >= wait_timeout:
                    break
                if speech_started and speech_started_at is not None and now - speech_started_at >= self.max_seconds:
                    break
                try:
                    block = chunks.get(timeout=0.12)
                except queue.Empty:
                    continue

                if now - waiting_started < ignore_first_seconds:
                    pre_roll.clear()
                    continue

                rms = float(np.sqrt(np.mean(np.square(block), dtype=np.float64)))
                if not speech_started:
                    pre_roll.append(block)

                if rms >= threshold:
                    if not speech_started:
                        speech_started = True
                        speech_started_at = now
                        frames.extend(pre_roll)
                        pre_roll.clear()
                    frames.append(block)
                    silent_for = 0.0
                elif speech_started:
                    frames.append(block)
                    silent_for += len(block) / self.sample_rate
                    if silent_for >= silence_seconds:
                        break

        audio = np.concatenate(frames) if frames else np.empty(0, dtype=np.float32)
        duration = len(audio) / self.sample_rate if len(audio) else 0.0
        return CaptureResult(audio=audio, duration=duration, speech_detected=speech_started)


class WhisperSTT:
    def __init__(self, model_name: str, device: str, compute_type: str, language: str) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None
        self._lock = threading.Lock()

    def preload(self) -> None:
        self._ensure_model()

    def _ensure_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from faster_whisper import WhisperModel

                    self._model = WhisperModel(
                        self.model_name,
                        device=self.device,
                        compute_type=self.compute_type,
                    )
        return self._model

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        model = self._ensure_model()
        lang = None if self.language.lower() in {"", "auto", "none"} else self.language
        segments, _info = model.transcribe(
            audio,
            language=lang,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
