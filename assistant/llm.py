from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ollama import Client

from assistant.config import AppConfig
from assistant.memory import MemoryStore
from assistant.tool_registry import ToolRegistry, ToolSpec


class LocalAgentLLM:
    def __init__(self, config: AppConfig, registry: ToolRegistry, memory: MemoryStore) -> None:
        self.config = config
        self.registry = registry
        self.memory = memory
        self.client = Client(host=config.ollama_host)
        self.history: list[dict[str, Any]] = []

    def _system_prompt(self, contact_aliases: list[str], app_aliases: list[str]) -> str:
        return f"""You are {self.config.assistant_name}, a local desktop voice assistant.

Voice behavior:
- The user is interacting by voice, so EVERY turn must end with a short natural sentence suitable for text-to-speech. Never intentionally return an empty final answer.
- Reply in the same language as the user's latest message unless asked otherwise.
- Be concise by default: usually one or two spoken sentences.
- After every tool call, explicitly tell the user whether it succeeded or failed and what happened. Examples: "Telegram message sent to Alex." / "I couldn't open Telegram." / "I opened the requested YouTube video."
- Never claim an external action succeeded unless the tool result says ok=true.
- If a tool fails, say that it failed and briefly state the returned reason when useful.

Agent behavior:
- When the user asks you to DO an available action, use the relevant tool instead of merely describing it.
- Distinguish visible browser actions from research: use web_search when the user wants the browser opened; use research_web when they want you to look something up, read sources, summarize, or answer from the web.
- Use read_webpage when the user gives a specific URL and asks what is on it or asks for a summary.
- Use open_youtube when the user wants a YouTube video/topic opened.
- Never invent a contact, application alias, URL, tool result, source content, or system status.
- If required information is missing, ask one short clarifying question.
- Use long-term memory only as background context; do not reveal hidden configuration values.
- Telegram messages are sent through the user's local Telegram Desktop UI, not a bot API.

Optional Telegram contact aliases: {contact_aliases or ['none']}
Configured application aliases: {app_aliases or ['none']}

Long-term memory:
{self.memory.summary()}
"""

    @staticmethod
    def _message_to_dict(message: Any) -> dict[str, Any]:
        if hasattr(message, "model_dump"):
            return message.model_dump(exclude_none=True)
        if isinstance(message, dict):
            return message
        return {"role": getattr(message, "role", "assistant"), "content": getattr(message, "content", "")}

    @staticmethod
    def _decode_tool_result(result: str) -> dict[str, Any]:
        try:
            parsed = json.loads(result)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except Exception:
            return {"value": result}

    def answer(
        self,
        user_text: str,
        contact_aliases: list[str],
        app_aliases: list[str],
        confirm: Callable[[ToolSpec, dict[str, Any]], bool] | None = None,
        on_tool: Callable[[str, dict[str, Any]], None] | None = None,
        on_tool_result: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt(contact_aliases, app_aliases)},
            *self.history[-12:],
            {"role": "user", "content": user_text},
        ]

        final_text = ""
        last_tool_result: dict[str, Any] | None = None
        last_tool_name = ""
        for _ in range(6):
            response = self.client.chat(
                model=self.config.ollama_model,
                messages=messages,
                tools=self.registry.schemas(),
                stream=False,
                options={"temperature": 0.15},
            )
            assistant_message = self._message_to_dict(response.message)
            messages.append(assistant_message)
            tool_calls = getattr(response.message, "tool_calls", None) or []

            if not tool_calls:
                final_text = (getattr(response.message, "content", "") or "").strip()
                break

            for call in tool_calls:
                name = call.function.name
                args = dict(call.function.arguments or {})
                if on_tool:
                    on_tool(name, args)
                result = self.registry.execute(name, args, confirm=confirm)
                decoded = self._decode_tool_result(result)
                last_tool_name, last_tool_result = name, decoded
                if on_tool_result:
                    on_tool_result(name, decoded)
                messages.append({"role": "tool", "content": result, "tool_name": name})
        else:
            final_text = "I stopped the action loop because too many tool steps were requested."

        # Deterministic spoken fallback: even if a local model emits a tool call
        # and then no final prose, the user still gets audible action feedback.
        if not final_text:
            if last_tool_result is not None:
                if last_tool_result.get("ok") is True:
                    final_text = f"Done. The {last_tool_name.replace('_', ' ')} action completed successfully."
                else:
                    reason = last_tool_result.get("error") or last_tool_result.get("message") or "the tool reported a failure"
                    final_text = f"I couldn't complete the {last_tool_name.replace('_', ' ')} action: {reason}."
            else:
                final_text = "I'm ready."

        # Hard guard for research integrity: if a web-reading tool failed, do not
        # allow the local model to replace failed research with uncited internal knowledge.
        if (
            last_tool_name in {"research_web", "read_webpage"}
            and last_tool_result is not None
            and last_tool_result.get("ok") is not True
        ):
            reason = last_tool_result.get("error") or "the web tool could not retrieve sources"
            final_text = f"I couldn't complete the web research because {reason}. I won't pretend I verified it online."

        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": final_text})
        self.history = self.history[-20:]
        return final_text
