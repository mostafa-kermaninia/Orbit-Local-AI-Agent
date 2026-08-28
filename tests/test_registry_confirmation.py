import json

from assistant.tool_registry import ToolRegistry, ToolSpec


def test_requires_confirmation_blocks_when_user_declines():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="side_effect",
            description="test",
            parameters={"type": "object", "properties": {}},
            handler=lambda: {"ok": True},
            requires_confirmation=True,
        )
    )

    result = json.loads(
        registry.execute(
            "side_effect",
            {},
            confirm=lambda _spec, _args: False,
        )
    )

    assert result["ok"] is False
    assert result["cancelled"] is True


def test_string_handler_result_is_normalised_to_success_object():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="remember_like",
            description="test",
            parameters={"type": "object", "properties": {}},
            handler=lambda: "Saved.",
        )
    )

    result = json.loads(registry.execute("remember_like", {}))
    assert result == {"ok": True, "message": "Saved."}
