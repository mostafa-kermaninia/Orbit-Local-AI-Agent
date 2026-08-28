from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class ToolSpec:
    """One explicit capability exposed to the local model.

    `requires_confirmation` describes policy, not implementation details:
    when confirmation is enabled in configuration, this tool must be approved
    before execution because it causes a real-world/local side effect.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]
    requires_confirmation: bool = False

    @property
    def external_write(self) -> bool:
        """Backward-compatible alias for older course notes/tests."""
        return self.requires_confirmation

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

    @staticmethod
    def _serialize_result(result: Any) -> str:
        # Normalise every tool result into an object with an explicit success
        # state. This makes fallback speech and tests deterministic.
        if isinstance(result, dict):
            payload = result
        elif isinstance(result, str):
            payload = {"ok": True, "message": result}
        elif result is None:
            payload = {"ok": True}
        else:
            payload = {"ok": True, "value": result}
        return json.dumps(payload, ensure_ascii=False, default=str)

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        confirm: Callable[[ToolSpec, dict[str, Any]], bool] | None = None,
    ) -> str:
        spec = self._tools.get(name)
        if spec is None:
            return json.dumps(
                {"ok": False, "error": f"Unknown tool: {name}"},
                ensure_ascii=False,
            )

        if (
            spec.requires_confirmation
            and confirm is not None
            and not confirm(spec, arguments)
        ):
            return json.dumps(
                {
                    "ok": False,
                    "cancelled": True,
                    "message": "User cancelled the action.",
                },
                ensure_ascii=False,
            )

        try:
            signature = inspect.signature(spec.handler)
            safe_args = {
                key: value
                for key, value in arguments.items()
                if key in signature.parameters
            }
            result = spec.handler(**safe_args)
            return self._serialize_result(result)
        except Exception as exc:
            return json.dumps(
                {"ok": False, "error": str(exc)},
                ensure_ascii=False,
            )
