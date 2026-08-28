# v4 - Reliable hands-free audio

- Default audio interaction mode is now `half_duplex`.
- The microphone is not opened while TTS is speaking, preventing self-trigger/echo loops.
- Continuous listening remains automatic: after TTS finishes, listening resumes immediately.
- `Esc` still interrupts TTS; the continuous loop then returns to listening.
- The previous threshold-only barge-in implementation is retained only as `experimental_barge_in` for headphones/AEC setups.
- HUD now labels the mode as `CONTINUOUS / MIC-GATED`.
