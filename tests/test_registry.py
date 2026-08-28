from assistant.tool_registry import ToolRegistry, ToolSpec


def test_registry_executes_known_tool():
    registry = ToolRegistry()
    registry.register(ToolSpec(
        name="echo",
        description="echo",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        handler=lambda text: {"ok": True, "text": text},
    ))
    result = registry.execute("echo", {"text": "hello", "ignored": 3})
    assert '"ok": true' in result.lower()
