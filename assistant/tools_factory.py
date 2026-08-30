from __future__ import annotations

from functools import partial

from assistant.config import AppConfig
from assistant.memory import MemoryStore
from assistant.tool_registry import ToolRegistry, ToolSpec
from tools.browser import open_url, read_webpage, research_web, web_search
from tools.system import SafeAppLauncher, system_status
from tools.telegram import TelegramDesktopMessenger
from tools.youtube import open_youtube


def build_registry(
    config: AppConfig,
    memory: MemoryStore,
) -> tuple[ToolRegistry, TelegramDesktopMessenger, SafeAppLauncher]:
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

    registry.register(
        ToolSpec(
            name="web_search",
            description=(
                "Visibly open a web search in the user's default browser. "
                "Use this when the user wants the browser opened, not when they "
                "want ORBIT to read and synthesize sources."
            ),
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=web_search,
        )
    )

    registry.register(
        ToolSpec(
            name="research_web",
            description=(
                "Search the public web, visibly open the search/results pages, "
                "read top public source pages, and return bounded evidence for "
                "multi-source synthesis."
            ),
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=partial(
                research_web,
                timeout_seconds=config.web_fetch_timeout_seconds,
                max_results=config.web_research_results,
                char_limit=config.web_page_char_limit,
                total_char_limit=config.web_total_char_limit,
                max_response_bytes=config.web_max_response_bytes,
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="read_webpage",
            description=(
                "Read the visible text of one specific public HTTP/HTTPS page. "
                "Private, loopback, link-local, and local-network addresses are blocked."
            ),
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            handler=partial(
                read_webpage,
                timeout_seconds=config.web_fetch_timeout_seconds,
                char_limit=config.web_page_char_limit,
                max_response_bytes=config.web_max_response_bytes,
            ),
        )
    )

    registry.register(
        ToolSpec(
            name="open_url",
            description="Open a normal HTTP/HTTPS URL in the user's default browser.",
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            handler=open_url,
        )
    )

    registry.register(
        ToolSpec(
            name="open_youtube",
            description=(
                "Find a requested video/topic on YouTube, open the first resolved "
                "result, and return its exact URL. If a later user-requested tool "
                "needs that link, use the returned url value exactly; never invent "
                "or guess a YouTube URL. Fall back to the YouTube search-results "
                "URL only when direct resolution fails."
            ),
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=open_youtube,
        )
    )

    registry.register(
        ToolSpec(
            name="send_telegram_message",
            description=(
                "Send exactly one Telegram message through the user's Telegram "
                "Desktop application. The tool issues the desktop send action; "
                "it does not independently verify server-side delivery."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "contact": {
                        "type": "string",
                        "description": "Contact/chat display name or configured alias",
                    },
                    "message": {
                        "type": "string",
                        "description": "Exact message requested by the user",
                    },
                },
                "required": ["contact", "message"],
            },
            handler=telegram.send,
            requires_confirmation=True,
        )
    )

    registry.register(
        ToolSpec(
            name="open_app",
            description=(
                "Open an application from the user's explicit configured app aliases. "
                "Never invent executable paths."
            ),
            parameters={
                "type": "object",
                "properties": {"app": {"type": "string"}},
                "required": ["app"],
            },
            handler=launcher.open,
            requires_confirmation=True,
        )
    )

    registry.register(
        ToolSpec(
            name="get_system_status",
            description="Read current CPU and memory utilization from this computer.",
            parameters={"type": "object", "properties": {}},
            handler=system_status,
        )
    )

    registry.register(
        ToolSpec(
            name="remember",
            description=(
                "Save a short fact to local long-term memory only when the user "
                "explicitly asks ORBIT to remember it."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["key", "value"],
            },
            handler=memory.remember,
        )
    )

    registry.register(
        ToolSpec(
            name="forget_memory",
            description="Remove a specific saved memory key when the user asks to forget it.",
            parameters={
                "type": "object",
                "properties": {"key": {"type": "string"}},
                "required": ["key"],
            },
            handler=memory.forget,
            requires_confirmation=True,
        )
    )

    return registry, telegram, launcher
