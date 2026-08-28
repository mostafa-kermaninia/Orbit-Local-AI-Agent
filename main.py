from __future__ import annotations

from assistant.config import load_config
from assistant.orchestrator import VoiceAssistant
from ui.app import OrbitUI


def main() -> None:
    config = load_config("config.json")
    assistant = VoiceAssistant(config)
    app = OrbitUI(config, assistant)
    app.mainloop()


if __name__ == "__main__":
    main()
