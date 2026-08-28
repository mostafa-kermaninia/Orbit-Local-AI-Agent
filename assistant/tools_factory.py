from __future__ import annotations

from functools import partial

from assistant.config import AppConfig
from assistant.memory import MemoryStore
from assistant.tool_registry import ToolRegistry, ToolSpec
from tools.browser import open_url, read_webpage, research_web, web_search
from tools.system import SafeAppLauncher, system_status
from tools.telegram import TelegramDesktopMessenger
from tools.youtube import open_youtube


def build_registry(config: AppConfig, memory: MemoryStore) -> tuple[ToolRegistry, TelegramDesktopMessenger, SafeAppLauncher]:
    registry = ToolRegistry()
    telegram = TelegramDesktopMessenger(
        executable=config.telegram_desktop_executable,
        contacts=config.telegram_contacts,
        launch_mode=config.telegram_launch_mode,
        launch_wait_seconds=config.telegram_launch_wait_seconds,
        search_wait_seconds=config.telegram_search_wait_seconds,
        chat_wait_seconds=config.telegram_chat_wait_seconds,
    )
    launcher = SafeAppLauncher(config.app_aliases)

    registry.register(ToolSpec(
        name="web_search",
        description="Visibly open a Google search in the user's default browser. Use when the user asks to search/open something in the browser, not when they ask you to research and summarize it yourself.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        handler=web_search,
    ))
    registry.register(ToolSpec(
        name="research_web",
        description="Search the public web, read a small number of top result pages, and return their text so you can answer or summarize. Use for 'look this up and tell me', current factual research, or website-content questions where opening the browser alone is insufficient.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        handler=partial(
            research_web,
            timeout_seconds=config.web_fetch_timeout_seconds,
            max_results=config.web_research_results,
            char_limit=config.web_page_char_limit,
        ),
    ))
    registry.register(ToolSpec(
        name="read_webpage",
        description="Read the visible text of a specific public http/https webpage so you can summarize or answer questions about that page.",
        parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        handler=partial(
            read_webpage,
            timeout_seconds=config.web_fetch_timeout_seconds,
            char_limit=config.web_page_char_limit,
        ),
    ))
    registry.register(ToolSpec(
        name="open_url",
        description="Open a normal http/https web address in the default browser.",
        parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
        handler=open_url,
    ))
    registry.register(ToolSpec(
        name="open_youtube",
        description="Find a requested video/topic on YouTube and open the first resolved result in the browser; fall back to YouTube search results if needed.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        handler=open_youtube,
    ))
    registry.register(ToolSpec(
        name="send_telegram_message",
        description=(
            "Send one Telegram message through the user's Telegram Desktop app. "
            "The Python tool opens/focuses Telegram, searches the requested contact/chat, "
            "opens the first matching result, pastes the message, and presses Enter."
        ),
        parameters={
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "Contact/chat display name or configured alias"},
                "message": {"type": "string", "description": "Exact message to send"},
            },
            "required": ["contact", "message"],
        },
        handler=telegram.send,
        # Intentional final-build behavior: an explicit voice/text command to
        # send a Telegram message executes immediately without an extra popup.
        external_write=False,
    ))
    registry.register(ToolSpec(
        name="open_app",
        description="Open an application from the user's explicit configured app aliases. Never invent executable paths.",
        parameters={"type": "object", "properties": {"app": {"type": "string"}}, "required": ["app"]},
        handler=launcher.open,
        external_write=True,
    ))
    registry.register(ToolSpec(
        name="get_system_status",
        description="Read current CPU and memory utilization from this computer.",
        parameters={"type": "object", "properties": {}},
        handler=system_status,
    ))
    registry.register(ToolSpec(
        name="remember",
        description="Save a short user-requested fact to long-term local memory when the user explicitly asks you to remember it.",
        parameters={
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            "required": ["key", "value"],
        },
        handler=memory.remember,
    ))
    registry.register(ToolSpec(
        name="forget_memory",
        description="Remove a specific saved memory key when the user asks to forget it.",
        parameters={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
        handler=memory.forget,
        external_write=True,
    ))
    return registry, telegram, launcher
