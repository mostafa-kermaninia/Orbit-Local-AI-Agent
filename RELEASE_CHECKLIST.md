# ORBIT Release Checklist

This repository package already contains the complete runtime. Do not copy only the documentation folders into another checkout with a recursive replacement command.

## Local validation

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

Copy-Item config.example.json config.json

python -m compileall -q assistant tools ui scripts main.py
python -m pytest -q
python main.py
```

Test these before publishing:

1. Voice transcription.
2. Spoken response.
3. System status.
4. Browser search.
5. Five-source visible web research.
6. YouTube.
7. Telegram Desktop message to a test contact.
8. Memory.
9. F2 pause/resume.
10. F8 interrupt.

## Git publication

Use this complete folder as the repository contents.

```powershell
git init
git branch -M main
git add .
git commit -m "release: ORBIT v1.0 course build"
git remote add origin https://github.com/mostafa-kermaninia/Orbit-Local-AI-Agent.git
git push -u origin main --force-with-lease
```

Only use the final push command after verifying that this local folder contains the exact code you want to publish.

For an existing clone, a safer alternative is to create a new branch first:

```powershell
git checkout -b restore-orbit-v1
git add .
git commit -m "release: restore ORBIT v1.0 course build"
git push -u origin restore-orbit-v1
```

Then inspect the branch on GitHub before replacing `main`.
