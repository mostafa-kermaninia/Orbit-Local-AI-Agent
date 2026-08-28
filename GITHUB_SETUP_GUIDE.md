# GitHub setup guide for ORBIT

These steps are performed in the GitHub web UI after committing the files in `repo_files/`.

## 1. Repository About

Open the repository → click the gear icon next to **About**.

### Description

Paste exactly:

> Local-first AI voice agent in Python: Whisper STT, Ollama/Qwen, tool calling, visible web research, Telegram Desktop automation, TTS, memory, and a real-time HUD.

### Website

Leave this blank until you have a real public course/project landing page. Do not use a placeholder URL.

### Topics

Add:

- python
- voice-assistant
- speech-recognition
- speech-processing
- faster-whisper
- ollama
- qwen
- local-ai
- ai-agent
- agentic-ai
- tool-calling
- desktop-automation
- telegram
- text-to-speech
- customtkinter
- windows

## 2. Social preview

Repository → **Settings** → **General** → **Social preview**.

Upload a clean 2:1 ORBIT dashboard/banner. Do not use a screenshot containing private Telegram names/messages.

A good target is 1280×640.

## 3. Features

Repository → **Settings** → **General** → **Features**.

Recommended:

- Issues: ON
- Discussions: ON
- Projects: optional / OFF unless you will use it
- Wiki: OFF (keep documentation versioned in `/docs`)
- Preserve this repository: optional

For Discussions, create or keep categories:

- Announcements
- Q&A
- Ideas
- Show and tell

Use **Q&A** for student usage questions instead of opening issues.

## 4. Pull request settings

Settings → General → Pull Requests:

- Allow squash merging: ON
- Default commit message for squash: Pull request title
- Automatically delete head branches: ON
- Allow merge commits: optional / OFF for a cleaner history
- Allow rebase merging: optional

## 5. Ruleset for `main`

Settings → Rules → Rulesets → New branch ruleset.

Name:

`Protect main`

Target:

`main`

Recommended rules:

- Block force pushes
- Restrict deletions
- Require status checks to pass
- Require branch to be up to date before merging
- Require linear history

After the CI workflow has run once, require these checks:

- `Python 3.11`
- `Python 3.12`

If you work alone, you do not need to require an approving review from another person.

## 6. Security

Settings → Security / Code security:

Enable when available:

- Dependabot alerts
- Dependabot security updates
- Secret scanning
- Push protection
- Private vulnerability reporting

The repository includes `.github/dependabot.yml`.

## 7. Labels

Create or keep these labels:

- `bug`
- `enhancement`
- `documentation`
- `course-question`
- `windows`
- `audio`
- `telegram`
- `web-research`
- `ui`
- `good first issue`

Suggested colors:

- course-question: `#6f42c1`
- windows: `#0078D4`
- audio: `#00A6A6`
- telegram: `#229ED9`
- web-research: `#2EA44F`
- ui: `#E99695`

## 8. First professional release

Create a release:

Tag:

`v1.0.0`

Release title:

`ORBIT v1.0.0 — Course Release`

Release body:

```markdown
## ORBIT v1.0.0

First stable course release of ORBIT, the local AI voice-agent final project for
«آموزش پروژه‌محور پردازش صوت و گفتار با پایتون».

### Highlights

- Local speech recognition with faster-whisper
- Local Ollama/Qwen reasoning and tool calling
- Hands-free half-duplex voice loop
- Spoken tool success/failure feedback
- Visible multi-source web research
- YouTube opening
- Telegram Desktop automation
- Safe application launcher
- Local memory
- Real-time HUD and telemetry

### Recommended environment

- Windows 10/11
- Python 3.11 or 3.12
- Ollama
- `qwen2.5:7b`
- Telegram Desktop for the Telegram demo

### Before running

Follow the Quick Start in `README.md` and run:

```powershell
python scripts/check_setup.py
```

See `docs/TROUBLESHOOTING.md` for common Windows, Whisper, network, and Telegram issues.
```

Mark the release as **Latest**.

## 9. Pin the repository

On your GitHub profile, pin `Orbit-Local-AI-Agent` so visitors immediately see the course project.

## 10. Commit history

After applying this pack, use meaningful commits. Example:

```text
docs: polish repository for v1.0 course release
ci: add Windows Python 3.11/3.12 test workflow
docs: add architecture and troubleshooting guides
chore: align course defaults with qwen2.5:7b
```

Avoid future commit messages such as `fix`, `final final`, `test2`, or `update files`.
