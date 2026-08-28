from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class MemoryStore:
    """Small explicit long-term memory store.

    It intentionally stores only facts requested through the remember tool.
    This keeps the behavior teachable and avoids silent collection of arbitrary data.
    """

    def __init__(self, path: str | Path = "data/memory.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text('{"facts": {}}', encoding="utf-8")

    def _read(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return {"facts": {}}
            raw.setdefault("facts", {})
            return raw
        except Exception:
            return {"facts": {}}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def remember(self, key: str, value: str) -> str:
        key = " ".join(key.strip().split())[:80]
        value = " ".join(value.strip().split())[:500]
        if not key or not value:
            return "Memory was not saved because key/value was empty."
        with self._lock:
            data = self._read()
            data["facts"][key] = value
            self._write(data)
        return f"Saved memory: {key} = {value}"

    def forget(self, key: str) -> str:
        with self._lock:
            data = self._read()
            existed = key in data["facts"]
            data["facts"].pop(key, None)
            self._write(data)
        return "Memory removed." if existed else "No matching memory existed."

    def summary(self, max_items: int = 20) -> str:
        with self._lock:
            facts = self._read().get("facts", {})
        if not facts:
            return "No saved long-term facts."
        items = list(facts.items())[-max_items:]
        return "\n".join(f"- {k}: {v}" for k, v in items)
