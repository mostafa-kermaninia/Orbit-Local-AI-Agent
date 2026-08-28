import json

from assistant.memory import MemoryStore


def test_corrupt_memory_is_backed_up_and_recovered(tmp_path):
    path = tmp_path / "memory.json"
    path.write_text("{broken json", encoding="utf-8")

    store = MemoryStore(path)
    assert store.summary() == "No saved long-term facts."

    backups = list(tmp_path.glob("memory.corrupt-*.json"))
    assert backups

    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed == {"facts": {}}


def test_memory_write_leaves_no_temp_file(tmp_path):
    path = tmp_path / "memory.json"
    store = MemoryStore(path)
    store.remember("project", "Aurora")

    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
