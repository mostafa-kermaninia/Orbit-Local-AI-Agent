# Maintainer Release Checklist

## 1. Validate on the Windows recording/release machine

```powershell
.\.venv\Scripts\Activate.ps1

python -m compileall -q assistant tools ui scripts main.py
python -m ruff check . --select E9,F63,F7,F82
python -m pytest -q
python scripts/check_setup.py
python main.py
```

Smoke-test:

1. microphone transcription;
2. TTS;
3. system telemetry;
4. browser search;
5. five-source visual research;
6. webpage reading;
7. YouTube;
8. memory;
9. Telegram with a non-sensitive test contact;
10. F2 pause/resume;
11. F8 interrupt.

## 2. Freeze the exact environment used for the recording

After the Windows smoke test passes:

```powershell
python -m pip freeze > requirements-lock.txt
```

Commit `requirements-lock.txt` only when it comes from the exact environment that was actually tested. Do not fabricate a lock file from guessed versions.

## 3. Update release metadata

Keep these aligned:

- `pyproject.toml`
- `CHANGELOG.md`
- `CITATION.cff`
- Git tag/release title

## 4. Create the GitHub Release

Recommended tag:

```text
v1.0.0
```

Course videos should point students to a specific Release, not to a moving `main` branch.
