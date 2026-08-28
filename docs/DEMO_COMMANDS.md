# Demo Commands

The commands below are intentionally chosen to demonstrate different layers of ORBIT.

## System telemetry

```text
What's my current CPU and RAM usage?
```

Demonstrates a read-only local tool.

## Visible web search

```text
Search Python asyncio TaskGroup in my browser.
```

Demonstrates browser control without pretending the LLM read the page.

## Multi-source research

```text
Research how Whisper works. Check the top five sources and summarize the main points.
```

Expected behavior:

- visible search page;
- visible source tabs;
- content extraction;
- synthesis from returned evidence;
- spoken summary.

## Specific webpage reading

```text
Read https://docs.python.org/3/library/asyncio-task.html and explain TaskGroup briefly.
```

## YouTube

```text
Open a Python asyncio tutorial on YouTube.
```

## Safe application launcher

```text
Open Notepad.
```

```text
Open Calculator.
```

## Long-term memory

```text
Remember that my demo project is called Aurora.
```

Then:

```text
What is my demo project called?
```

And:

```text
Forget my demo project name.
```

## Telegram Desktop

Use a non-sensitive test contact:

```text
Send a Telegram message to Amir saying: hey, how are you?
```

For a recorded demo, use a distinctive contact/chat name so the first search result is deterministic.

## Recommended recording sequence

```text
1. System status
2. Browser search
3. Multi-source research
4. YouTube
5. Memory
6. Telegram
```

This sequence moves from read-only local tools toward visible external actions.
