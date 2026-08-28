import json

from assistant.config import AppConfig, load_config


def test_public_defaults_are_safe_and_reproducible(tmp_path):
    path = tmp_path / "config.json"
    config = load_config(path)

    assert config.ollama_model == "qwen2.5:7b"
    assert config.confirm_external_actions is True
    assert config.web_research_results == 5
    assert config.web_total_char_limit == 18_000


def test_unknown_config_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "assistant_name": "TEST",
                "unknown_future_key": 123,
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)
    assert config.assistant_name == "TEST"
    assert not hasattr(config, "unknown_future_key")
