# ORBIT — دستیار صوتی Local AI

[English README](README.md)

ORBIT یک پروژه آموزشی و Local-first برای ساخت یک Voice Agent کامل با پایتون است؛ پروژه‌ای که ورودی میکروفون را با Whisper به متن تبدیل می‌کند، تصمیم‌گیری و Tool Calling را با یک مدل محلی روی Ollama انجام می‌دهد و نتیجه را از طریق TTS به کاربر برمی‌گرداند.

این مخزن پروژه نهایی دوره **«آموزش پروژه‌محور پردازش صوت و گفتار با پایتون»** است و توسط **Mostafa Kermaninia** نگه‌داری می‌شود.

## معماری کلی

```text
Microphone
   ↓
faster-whisper (STT)
   ↓
Ollama / Qwen2.5
   ↓
Tool Registry
   ├── Web Research
   ├── Read Webpage
   ├── YouTube
   ├── Telegram Desktop
   ├── App Launcher
   ├── System Status
   └── Local Memory
   ↓
Windows SAPI / pyttsx3
   ↓
Speaker
```

## قابلیت‌ها

- تشخیص گفتار لوکال با `faster-whisper`
- مدل زبانی لوکال با Ollama
- Tool Calling با زبان طبیعی
- Continuous Listening بدون نیاز به زدن دکمه Listen
- حالت پیش‌فرض Half-Duplex برای جلوگیری از شنیدن صدای خود دستیار
- باز کردن Search در مرورگر
- Research چندمنبعی و باز کردن Sourceها در Tabهای واقعی مرورگر
- خواندن و خلاصه‌سازی یک URL عمومی
- باز کردن ویدیو یا موضوع در YouTube
- ارسال پیام با Telegram Desktop از طریق UI خود سیستم
- حافظه بلندمدت ساده روی JSON
- نمایش CPU/RAM/Network
- HUD گرافیکی Real-time

## نصب سریع روی Windows

```powershell
git clone https://github.com/mostafa-kermaninia/Orbit-Local-AI-Agent.git
cd Orbit-Local-AI-Agent

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

ollama pull qwen2.5

Copy-Item config.example.json config.json
python scripts/check_setup.py
python main.py
```

اگر PowerShell اجازه فعال‌سازی venv را نداد:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## کنترل‌ها

| کلید | عملکرد |
|---|---|
| `F2` | Pause / Resume برای Continuous Listening |
| `F8` | قطع صدای فعلی دستیار و Reset کردن Audio Pipeline |

`Esc` برای Automation تلگرام آزاد نگه داشته شده است.

## چند دستور برای تست

```text
What's my current CPU and RAM usage?

Search Python asyncio tutorial in my browser.

Research how Whisper works. Check the top five sources and summarize them.

Open a Python asyncio tutorial on YouTube.

Open Notepad.

Remember that my demo project is called Aurora.

Send a Telegram message to Amir saying: hey, how are you?
```

## تلگرام

ORBIT از Bot API استفاده نمی‌کند. ابزار تلگرام روی Windows، برنامه Telegram Desktop را باز می‌کند، نام مخاطب را جست‌وجو می‌کند، پیام را Paste می‌کند و Enter می‌زند.

برای Demo پایدار، از یک Contact آزمایشی با اسم مشخص استفاده کن.

## نکته مهم درباره صدا

حالت پیشنهادی پروژه:

```json
"audio_interaction_mode": "half_duplex",
"barge_in_enabled": false
```

در این حالت وقتی ORBIT در حال صحبت است، میکروفون Gate می‌شود و صدای خود دستیار دوباره به‌عنوان صدای کاربر تشخیص داده نمی‌شود.

## مدل پیشنهادی

برای نسخه دوره:

```powershell
ollama pull qwen2.5
```

Tool Calling می‌تواند بین مدل‌ها و Quantizationهای مختلف تفاوت داشته باشد؛ بنابراین برای ضبط یا Release دقیقاً همان مدلی را تست کن که در `config.json` ثبت شده است.

## مستندات بیشتر

- [معماری فنی](docs/ARCHITECTURE.md)
- [دستورات Demo](docs/DEMO_COMMANDS.md)
- [راهنمای تدریس](docs/COURSE_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security](SECURITY.md)
- [Provenance](PROVENANCE.md)

## مجوز

کد ORBIT تحت [MIT License](LICENSE) منتشر شده است.

Dependencyها، مدل‌های Ollama و سایر نرم‌افزارهای Third-party لایسنس مستقل خودشان را دارند. جزئیات در [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) آمده است.
