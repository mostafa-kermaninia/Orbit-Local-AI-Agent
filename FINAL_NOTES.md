# ORBIT Final Course Build

This build deliberately restores the Telegram Desktop interaction sequence from
V2, because that exact sequence was verified on the target Windows machine.

## Telegram flow

1. Windows key
2. Type `Telegram`
3. Enter
4. Focus Telegram best-effort
5. Escape twice
6. Ctrl+F
7. Paste contact name
8. Down + Enter
9. Paste message
10. Enter to send

There is no confirmation dialog for Telegram in this build.

## Important hands-free change

ORBIT uses **F8** for manual interrupt instead of Escape. Telegram uses Escape
inside its own navigation, so reserving Escape for the desktop automation avoids
self-interrupting ORBIT.

## Audio

The default interaction mode remains `half_duplex`: the microphone is not open
while TTS is speaking, preventing the assistant from hearing itself. Listening
resumes automatically after speech ends.
