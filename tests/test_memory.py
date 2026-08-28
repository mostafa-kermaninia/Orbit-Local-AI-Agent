from pathlib import Path

from assistant.memory import MemoryStore


def test_memory_roundtrip(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory.json")
    store.remember("project", "Aurora")
    assert "Aurora" in store.summary()
    assert "removed" in store.forget("project").lower()
