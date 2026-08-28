from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import httpx


def main() -> int:
    print("Python:", sys.version.split()[0])
    print("Ollama executable:", shutil.which("ollama") or "NOT FOUND")

    cfg = json.loads(Path("config.json").read_text(encoding="utf-8")) if Path("config.json").exists() else {}
    host = cfg.get("ollama_host", "http://127.0.0.1:11434")
    model = cfg.get("ollama_model", "qwen2.5")
    try:
        response = httpx.get(host.rstrip("/") + "/api/tags", timeout=3)
        response.raise_for_status()
        names = [m.get("name") for m in response.json().get("models", [])]
        print("Ollama server: OK")
        print("Configured model:", model, "FOUND" if any(n == model or str(n).startswith(model + ":") for n in names) else "NOT FOUND")
        print("Installed models:", ", ".join(filter(None, names)) or "none")
    except Exception as exc:
        print("Ollama server: FAILED -", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
