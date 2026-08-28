from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    external_write: bool = False

    def ollama_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Duplicate tool: {spec.name}")
        self._tools[spec.name] = spec

    def schemas(self) -> list[dict[str, Any]]:
        return [spec.ollama_schema() for spec in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools)

    def spec(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        confirm: Callable[[ToolSpec, dict[str, Any]], bool] | None = None,
    ) -> str:
        spec = self._tools.get(name)
        if spec is None:
            return json.dumps({"ok": False, "error": f"Unknown tool: {name}"}, ensure_ascii=False)

        if spec.external_write and confirm is not None and not confirm(spec, arguments):
            return json.dumps({"ok": False, "cancelled": True, "message": "User cancelled the action."}, ensure_ascii=False)

        try:
            signature = inspect.signature(spec.handler)
            safe_args = {k: v for k, v in arguments.items() if k in signature.parameters}
            result = spec.handler(**safe_args)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
