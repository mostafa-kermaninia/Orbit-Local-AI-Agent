from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any


class MemoryStore:
    """Small explicit long-term memory store with atomic persistence."""

    def __init__(self, path: str | Path = "data/memory.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

        if not self.path.exists():
            self._write({"facts": {}})

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"facts": {}}

    def _backup_corrupt_file(self) -> Path | None:
        if not self.path.exists():
            return None
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(
            f"{self.path.stem}.corrupt-{timestamp}{self.path.suffix}"
        )
        try:
            os.replace(self.path, backup)
            return backup
        except OSError:
            return None

    def _read(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("memory root is not an object")
            facts = raw.get("facts")
            if not isinstance(facts, dict):
                raise ValueError("memory facts is not an object")
            return raw
        except FileNotFoundError:
            data = self._empty()
            self._write(data)
            return data
        except Exception:
            # Preserve the broken file instead of silently overwriting evidence
            # of corruption, then continue with a fresh valid store.
            self._backup_corrupt_file()
            data = self._empty()
            self._write(data)
            return data

    def _write(self, data: dict[str, Any]) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")

        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp, self.path)

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
        key = " ".join(key.strip().split())[:80]
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
        return "\n".join(f"- {key}: {value}" for key, value in items)
